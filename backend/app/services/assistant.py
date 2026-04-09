"""
AI assistant service powered by OpenRouter (meta-llama/llama-3.1-8b-instruct).
Handles natural-language booking requests by executing tools against the database.
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.booking import Booking, BookingStatus
from app.models.resource import Resource, ResourceStatus
from app.services.booking import cancel_booking, create_booking

_client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "mistralai/mistral-nemo"

SYSTEM_PROMPT = """You are a friendly, smart booking assistant for a university campus.
You help with study rooms, washing machines, and dryers — nothing else.
Today: {today}. This user lives in {user_dorm}.

Your job is to understand what the user wants and get it done with minimal back-and-forth.
Respond naturally, like a helpful person — not like a bot reading from a script.

── UNDERSTANDING REQUESTS ──
Read intent, not just keywords. Examples:
  "book a washer at 10 tomorrow"        → book_random(washing_machine, tomorrow, 10, count=1)
  "book me 3 random study rooms at 14"  → book_random(study_room, date, 14, count=3)
  "random one from d6"                  → book_random(..., location_hint="Dorm 6", count=1)
  "pick one from dorm 3"                → book_random(..., location_hint="Dorm 3", count=1)
  "my dorm" / "my building"             → location_hint="{user_dorm}" (never ask which dorm)
  "book d7-f6 washer at 10"             → book_by_name("D7-F6", ..., category="washing_machine")
  "what study rooms are free tomorrow?" → find_available_resources(study_room, date)

Dorm shorthand: "d1"=Dorm 1, "d6"=Dorm 6, "dorm3"=Dorm 3, "3rd dorm"=Dorm 3, etc.

── WHEN TO LIST vs WHEN TO BOOK ──
- "book me a washer" with no dorm/floor hint → find_available_resources, show list, let user pick
- "book me a washer in d6" or "pick one" or "random" → book_random immediately, no listing
- User picks from a list you showed → book_by_name or book_random with location_hint

── TOOL ERRORS ──
book_by_name "not_found" → name didn't match, ask user to clarify (don't say it's taken)
book_by_name "all_taken" → suggest next free time or different floor
book_random "all_taken"  → say nothing's free at that time, suggest alternatives

── STYLE ──
- Confirm bookings with: name, location, date, time. Short sentence, friendly tone.
- If something fails, be direct about why and suggest what to do next.
- Never show IDs or UUIDs.
- Decline politely if asked about anything unrelated to campus bookings.
"""

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "find_available_resources",
            "description": "Find campus resources of a given category that have free slots on a specific date. Returns up to 5 resources with available times. Pass location_hint (e.g. 'Dorm 3') to filter by dorm. Without location_hint, returns one result per dorm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["study_room", "washing_machine", "dryer", "meeting_room", "rest_area"],
                        "description": "Type of resource to find",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "location_hint": {
                        "type": "string",
                        "description": "Optional location filter, e.g. 'Dorm 3' or 'Dorm 7'. Use when user specifies a dorm.",
                    },
                },
                "required": ["category", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_resources",
            "description": "Returns all campus resources. Use find_available_resources instead when you need to book something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["study_room", "washing_machine", "dryer", "meeting_room", "rest_area"],
                        "description": "Optional: filter by resource category",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_random",
            "description": "Books N random available resources. Use when user says 'random', 'pick one', 'book me a washer', 'from d6', etc. Filters by dorm if location_hint given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["study_room", "washing_machine", "dryer", "meeting_room", "rest_area"],
                    },
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "hour": {"type": "integer", "description": "Start hour (0-23), e.g. 10 for 10:00"},
                    "count": {"type": "integer", "description": "Number of resources to book (default 1)"},
                    "duration_hours": {"type": "integer", "description": "Duration in hours (default 1)"},
                    "location_hint": {"type": "string", "description": "Optional dorm filter, e.g. 'Dorm 6'. Use when user says 'from d6', 'in dorm 3', 'my dorm', etc."},
                },
                "required": ["category", "date", "hour"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_by_name",
            "description": "Books a resource by name or partial name. Pass category to avoid ambiguity when user says things like 'd7-f6'. If D7-F6-1 is taken, automatically tries D7-F6-2. Returns success or a clear error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string", "description": "Resource name or partial name, e.g. 'Washer D7-F6-1', 'D7-F6', 'd7 f6'"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "hour": {"type": "integer", "description": "Start hour (0-23), e.g. 10 for 10:00"},
                    "category": {
                        "type": "string",
                        "enum": ["washing_machine", "dryer", "study_room", "meeting_room", "rest_area"],
                        "description": "Resource category — REQUIRED when user mentions 'washer', 'dryer', 'study room', etc. to avoid wrong matches.",
                    },
                    "duration_hours": {"type": "integer", "description": "Duration in hours (default 1)"},
                },
                "required": ["resource_name", "date", "hour"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancels an existing confirmed booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "UUID of the booking to cancel"},
                },
                "required": ["booking_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_my_bookings",
            "description": "Returns the current user's upcoming confirmed bookings.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


async def _execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    db: AsyncSession,
    user_id: uuid.UUID,
    user_name: str = "",
) -> str:
    try:
        if tool_name == "find_available_resources":
            category_filter = tool_input["category"]
            date_param = date.fromisoformat(tool_input["date"])
            location_hint = tool_input.get("location_hint", "").strip().lower()
            tz = timezone.utc
            day_start = datetime(date_param.year, date_param.month, date_param.day, 0, 0, tzinfo=tz)
            day_end = datetime(date_param.year, date_param.month, date_param.day, 23, 0, tzinfo=tz)

            # Get resources in this category
            query = (
                select(Resource)
                .where(Resource.status == ResourceStatus.available, Resource.category == category_filter)
                .order_by(Resource.location, Resource.name)
            )
            if location_hint:
                query = query.where(func.lower(Resource.location).contains(location_hint))
            res_result = await db.execute(query)
            resources = res_result.scalars().all()
            if not resources:
                return json.dumps({"results": [], "note": "No available resources found."})

            resource_ids = [r.id for r in resources]
            bk_result = await db.execute(
                select(Booking).where(
                    and_(
                        Booking.resource_id.in_(resource_ids),
                        Booking.status == BookingStatus.confirmed,
                        Booking.starts_at < day_end + timedelta(hours=1),
                        Booking.ends_at > day_start,
                    )
                )
            )
            all_bookings = bk_result.scalars().all()

            # Build per-resource availability
            available_resources = []
            for r in resources:
                r_bookings = [b for b in all_bookings if b.resource_id == r.id]
                free_slots = []
                current = day_start
                while current + timedelta(hours=1) <= day_end + timedelta(hours=1):
                    slot_end = current + timedelta(hours=1)
                    if not any(b.starts_at < slot_end and b.ends_at > current for b in r_bookings):
                        free_slots.append(current.strftime("%H:%M"))
                    current = slot_end
                if free_slots:
                    available_resources.append({
                        "resource_id": str(r.id),
                        "name": r.name,
                        "location": r.location,
                        "free_slots": free_slots,
                    })

            # Without location_hint: return one result per dorm (up to 7)
            if not location_hint:
                seen_dorms: set[str] = set()
                output = []
                for item in available_resources:
                    dorm_key = item["location"].split(",")[0]  # e.g. "Dorm 1"
                    if dorm_key not in seen_dorms:
                        seen_dorms.add(dorm_key)
                        output.append(item)
                    if len(output) >= 7:
                        break
                note = "Showing one option per dorm. If user wants a specific dorm, call again with location_hint='Dorm X'."
            else:
                output = available_resources[:5]
                note = f"Showing up to 5 results for '{location_hint}'."

            return json.dumps({"results": output, "note": note}, ensure_ascii=False)

        elif tool_name == "book_random":
            category_filter = tool_input["category"]
            date_param = date.fromisoformat(tool_input["date"])
            hour = int(tool_input["hour"])
            count = int(tool_input.get("count", 1))
            duration = int(tool_input.get("duration_hours", 1))
            location_hint = tool_input.get("location_hint", "").strip().lower()

            tz = timezone.utc
            starts_at = datetime(date_param.year, date_param.month, date_param.day, hour, 0, tzinfo=tz)
            ends_at = starts_at + timedelta(hours=duration)

            # Get all available resources in category, optionally filtered by dorm
            query = (
                select(Resource)
                .where(Resource.status == ResourceStatus.available, Resource.category == category_filter)
                .order_by(Resource.location, Resource.name)
            )
            if location_hint:
                query = query.where(func.lower(Resource.location).contains(location_hint))
            res_result = await db.execute(query)
            all_resources = list(res_result.scalars().all())
            if not all_resources:
                return json.dumps({"error": "no_resources", "message": f"No {category_filter} resources found."})

            # Get existing bookings at this slot
            resource_ids = [r.id for r in all_resources]
            bk_result = await db.execute(
                select(Booking.resource_id).where(
                    Booking.resource_id.in_(resource_ids),
                    Booking.status == BookingStatus.confirmed,
                    Booking.starts_at < ends_at,
                    Booking.ends_at > starts_at,
                )
            )
            taken_ids = {row[0] for row in bk_result.all()}

            # Filter to free resources, shuffle for randomness
            free_resources = [r for r in all_resources if r.id not in taken_ids]
            random.shuffle(free_resources)

            if not free_resources:
                return json.dumps({"error": "all_taken", "message": f"All {category_filter} resources are booked at {hour:02d}:00."})

            # Book up to count resources
            booked = []
            for resource in free_resources[:count]:
                booking = await create_booking(db, user_id, resource.id, starts_at, ends_at, None, user_name)
                booked.append({"resource": resource.name, "location": resource.location})

            return json.dumps({
                "booked": booked,
                "count": len(booked),
                "requested": count,
                "date": date_param.isoformat(),
                "time": f"{hour:02d}:00\u2013{(hour + duration) % 24:02d}:00",
                "note": "" if len(booked) == count else f"Only {len(booked)} were available (requested {count}).",
            }, ensure_ascii=False)

        elif tool_name == "book_by_name":
            resource_name = tool_input["resource_name"].strip()
            date_param = date.fromisoformat(tool_input["date"])
            hour = int(tool_input["hour"])
            duration = int(tool_input.get("duration_hours", 1))
            explicit_category = tool_input.get("category")

            tz = timezone.utc
            starts_at = datetime(date_param.year, date_param.month, date_param.day, hour, 0, tzinfo=tz)
            ends_at = starts_at + timedelta(hours=duration)

            # Build category filter (explicit > inferred from name)
            def _cat_condition(name_lower: str):
                if explicit_category:
                    return Resource.category == explicit_category
                if any(w in name_lower for w in ("washer", "washing")):
                    return Resource.category == "washing_machine"
                if "dryer" in name_lower or "dry" in name_lower:
                    return Resource.category == "dryer"
                if "study" in name_lower:
                    return Resource.category == "study_room"
                return None  # no category filter

            name_lower = resource_name.lower()
            cat_cond = _cat_condition(name_lower)

            # 1. Exact match first (case-insensitive)
            exact_filters = [
                func.lower(Resource.name) == name_lower,
                Resource.status == ResourceStatus.available,
            ]
            if cat_cond is not None:
                exact_filters.append(cat_cond)
            res_result = await db.execute(select(Resource).where(*exact_filters))
            candidates = list(res_result.scalars().all())

            # 2. Fuzzy fallback: strip category words, search by location/id fragment
            if not candidates:
                search_term = name_lower
                for word in ("washing machine", "washer", "dryer", "study room", "meeting room", "rest area"):
                    search_term = search_term.replace(word, " ")
                # Also replace "dorm X floor Y" → "dX-fY" style for better matching
                import re as _re
                search_term = _re.sub(r"dorm\s*(\d+)\s*floor\s*(\d+)", r"d\1-f\2", search_term)
                search_term = search_term.strip()

                fuzzy_filters = [
                    func.lower(Resource.name).contains(search_term),
                    Resource.status == ResourceStatus.available,
                ]
                if cat_cond is not None:
                    fuzzy_filters.append(cat_cond)

                res_result2 = await db.execute(
                    select(Resource).where(*fuzzy_filters).order_by(Resource.name)
                )
                candidates = list(res_result2.scalars().all())

            if not candidates:
                return json.dumps({
                    "error": "not_found",
                    "message": f"No resource matching '{resource_name}' found. Ask the user to pick from the list.",
                })

            # 3. Try each candidate in order — book first available slot
            booked_names = []
            for resource in candidates:
                conflict_res = await db.execute(
                    select(Booking).where(
                        Booking.resource_id == resource.id,
                        Booking.status == BookingStatus.confirmed,
                        Booking.starts_at < ends_at,
                        Booking.ends_at > starts_at,
                    )
                )
                if conflict_res.scalar_one_or_none():
                    booked_names.append(resource.name)
                    continue

                # Free — book it
                booking = await create_booking(db, user_id, resource.id, starts_at, ends_at, None, user_name)
                return json.dumps({
                    "error": "success",
                    "resource": resource.name,
                    "location": resource.location,
                    "date": date_param.isoformat(),
                    "time": f"{hour:02d}:00\u2013{(hour + duration) % 24:02d}:00",
                }, ensure_ascii=False)

            # All candidates are taken at that time — find next free slot for first candidate
            first = candidates[0]
            next_free = None
            for try_hour in range(7, 23):
                if try_hour == hour:
                    continue
                s = datetime(date_param.year, date_param.month, date_param.day, try_hour, 0, tzinfo=tz)
                e = s + timedelta(hours=duration)
                c = await db.execute(
                    select(Booking).where(
                        Booking.resource_id == first.id,
                        Booking.status == BookingStatus.confirmed,
                        Booking.starts_at < e,
                        Booking.ends_at > s,
                    )
                )
                if not c.scalar_one_or_none():
                    next_free = f"{try_hour:02d}:00"
                    break

            return json.dumps({
                "error": "all_taken",
                "message": f"All matching resources ({', '.join(booked_names)}) are booked at {hour:02d}:00.",
                "suggestion": f"Next free slot for {first.name}: {next_free}" if next_free else "No free slots today.",
            }, ensure_ascii=False)

        elif tool_name == "list_resources":
            category_filter = tool_input.get("category")
            query = select(Resource).where(Resource.status != ResourceStatus.retired)
            if category_filter:
                query = query.where(Resource.category == category_filter)
            query = query.order_by(Resource.category, Resource.location, Resource.name)
            result = await db.execute(query)
            resources = result.scalars().all()
            # Return compact representation to stay within context limits
            items = [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "category": r.category.value,
                    "location": r.location,
                    "status": r.status.value,
                }
                for r in resources
            ]
            return json.dumps(items, ensure_ascii=False)

        elif tool_name == "get_availability":
            resource_id = uuid.UUID(tool_input["resource_id"])
            date_param = date.fromisoformat(tool_input["date"])
            tz = timezone.utc
            day_start = datetime(date_param.year, date_param.month, date_param.day, 0, 0, tzinfo=tz)
            day_end = datetime(date_param.year, date_param.month, date_param.day, 23, 0, tzinfo=tz)

            result = await db.execute(
                select(Booking).where(
                    Booking.resource_id == resource_id,
                    Booking.status == BookingStatus.confirmed,
                    Booking.starts_at >= day_start,
                    Booking.ends_at <= day_end + timedelta(hours=1),
                )
            )
            bookings = result.scalars().all()

            slots = []
            current = day_start
            while current + timedelta(hours=1) <= day_end + timedelta(hours=1):
                slot_end = current + timedelta(hours=1)
                is_booked = any(b.starts_at < slot_end and b.ends_at > current for b in bookings)
                if not is_booked:
                    slots.append({"starts_at": current.isoformat(), "ends_at": slot_end.isoformat()})
                current = slot_end

            return json.dumps(slots, ensure_ascii=False)

        elif tool_name == "create_booking":
            resource_id = uuid.UUID(tool_input["resource_id"])
            starts_at = datetime.fromisoformat(tool_input["starts_at"])
            ends_at = datetime.fromisoformat(tool_input["ends_at"])
            notes = tool_input.get("notes")
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=timezone.utc)
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)

            booking = await create_booking(db, user_id, resource_id, starts_at, ends_at, notes, user_name)
            return json.dumps(
                {
                    "id": str(booking.id),
                    "starts_at": booking.starts_at.isoformat(),
                    "ends_at": booking.ends_at.isoformat(),
                    "status": booking.status.value,
                },
                ensure_ascii=False,
            )

        elif tool_name == "cancel_booking":
            booking_id = uuid.UUID(tool_input["booking_id"])
            result = await db.execute(
                select(Booking).where(
                    Booking.id == booking_id,
                    Booking.user_id == user_id,
                    Booking.status == BookingStatus.confirmed,
                )
            )
            booking = result.scalar_one_or_none()
            if not booking:
                return json.dumps({"error": "Booking not found or already cancelled"})
            await cancel_booking(db, booking)
            return json.dumps({"cancelled": True, "booking_id": str(booking_id)})

        elif tool_name == "list_my_bookings":
            now = datetime.now(tz=timezone.utc)
            result = await db.execute(
                select(Booking, Resource)
                .join(Resource, Booking.resource_id == Resource.id)
                .where(
                    Booking.user_id == user_id,
                    Booking.status == BookingStatus.confirmed,
                    Booking.ends_at > now,
                )
                .order_by(Booking.starts_at)
            )
            rows = result.all()
            items = [
                {
                    "id": str(b.id),
                    "resource_name": r.name,
                    "resource_id": str(b.resource_id),
                    "starts_at": b.starts_at.isoformat(),
                    "ends_at": b.ends_at.isoformat(),
                }
                for b, r in rows
            ]
            return json.dumps(items, ensure_ascii=False)

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Tool error: {str(e)}"})


async def run_assistant(
    db: AsyncSession,
    user_id: uuid.UUID,
    messages: list[dict[str, str]],
    user_name: str = "",
    user_building: int | None = None,
) -> str:
    """
    Runs the assistant with tool-use loop via OpenRouter.
    messages: list of {role, content} dicts from the frontend conversation history.
    Returns the final text reply.
    """
    today = datetime.now(tz=timezone.utc).date().isoformat()
    user_dorm = f"Dorm {user_building}" if user_building else "unknown"

    api_messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT.format(today=today, user_dorm=user_dorm)},
        *[{"role": m["role"], "content": m["content"]} for m in messages],
    ]

    from openai import APIStatusError

    for _ in range(10):  # max tool-use rounds
        try:
            response = await _client.chat.completions.create(
                model=MODEL,
                messages=api_messages,  # type: ignore[arg-type]
                tools=TOOLS,  # type: ignore[arg-type]
                tool_choice="auto",
            )
        except APIStatusError as e:
            if e.status_code in (502, 503, 529):
                return "The AI service is temporarily unavailable. Please try again in a moment."
            raise

        choice = response.choices[0]
        msg = choice.message

        if choice.finish_reason == "stop" or not msg.tool_calls:
            return msg.content or ""

        # Append assistant message with tool calls
        api_messages.append(msg)  # type: ignore[arg-type]

        # Execute tools and append results
        for tc in msg.tool_calls:
            tool_input = json.loads(tc.function.arguments)
            result = await _execute_tool(tc.function.name, tool_input, db, user_id, user_name)
            api_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return "Could not get a response."
