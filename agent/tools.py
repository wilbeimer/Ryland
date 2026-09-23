TOOLS = [
    {
        "name": "create_course",
        "description": "Creates a new course and adds it to the database",
        "input_schema": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "The name of the course"
                },
                "course_description": {
                    "type": "string",
                    "description": "A detailed description of the course"
                }
            },
            "required": ["course_name", "course_description"]
        }
    },
    {
        "name": "ask_user",
        "description": "Ask the user a clarifying question when the request is missing information you need. Use this instead of guessing.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    }

]
