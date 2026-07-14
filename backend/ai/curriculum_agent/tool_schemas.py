TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "set_course_description",
            "description": "Set the course description, subject domain, subdomains, and prerequisites. Call this first, before anything else.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "domain": {"type": "string", "description": "Broad subject area, e.g. 'Computer Science'"},
                    "subdomains": {"type": "array", "items": {"type": "string"}},
                    "prerequisites": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_course_length",
            "description": "Set overall course duration. Call before creating any weeks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_weeks": {"type": "integer"},
                    "hours_per_week": {"type": "integer"},
                },
                "required": ["duration_weeks", "hours_per_week"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_textbook",
            "description": "Attach a required textbook to the course. Only call this if the course genuinely requires one — skip it otherwise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "edition": {"type": "string"},
                    "publisher": {"type": "string"},
                    "isbn": {"type": "string"},
                    "link": {"type": "string"},
                },
                "required": ["title", "authors"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_week",
            "description": "Create a single week with its learning goal and topics. Call once per week, in ascending order starting at 1. Returns the week's internal id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_number": {"type": "integer"},
                    "goal": {"type": "string", "description": "What the learner can do by end of week"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["week_number", "goal", "topics"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_assignment",
            "description": "Add a fully-specified assignment to an existing week. The week must already exist (call create_week first). Fill in every field in this one call — there is no separate 'add details' step. Returns the assignment's id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "type": {"type": "string", "enum": ["written", "checklist", "project", "presentation"]},
                    "description": {"type": "string"},
                    "requirements": {"type": "array", "items": {"type": "string"}},
                    "resources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "source": {"type": "string", "enum": ["textbook", "youtube", "web", "article"]},
                            },
                            "required": ["title", "url"],
                        },
                    },
                    "dueDate": {"type": "string", "description": "ISO date or relative phrase like 'end of week 3'"},
                    "points": {"type": "number"},
                    "rubric": {"type": "string"},
                },
                "required": ["week_number", "title", "type", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_quiz",
            "description": "Set the quiz for a week. Each week has at most one quiz — calling this again for the same week fails unless replace=true.",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "type": {"type": "string", "enum": ["weekly", "midterm", "final", "review"]},
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["multiple_choice", "short_answer"]},
                                "prompt": {"type": "string"},
                                "choices": {"type": "array", "items": {"type": "string"}, "description": "Required for multiple_choice, omit for short_answer"},
                                "answer": {"type": "string"},
                            },
                            "required": ["type", "prompt", "answer"],
                        },
                    },
                    "dueDate": {"type": "string"},
                    "points": {"type": "number"},
                    "replace": {"type": "boolean", "description": "Set true to overwrite an existing quiz for this week"},
                },
                "required": ["week_number", "title", "type", "questions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Search YouTube for a candidate video resource. Returns up to max_results candidates with title, url, channel, and description. Pick one and pass its title/url into create_assignment's resources with source='youtube' — don't pass the raw search result through directly, it has extra fields Resource doesn't accept.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "description": "Default 2"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_course",
            "description": "Call once every week has a goal/topics and at least one assignment. Marks the course complete. If it returns an error, it will list what's missing — fix that and call it again.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

