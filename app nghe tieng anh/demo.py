from project import build_sample_library


def demo():
    print("=" * 60)
    print("English Listening App Demo")
    print("=" * 60)

    app, _ = build_sample_library()

    print("\nLevel 1 Lessons:")
    for lesson in app.get_lessons_by_level("Level1"):
        print(f"  {lesson}")

    print("\nStarting lesson 1...")
    app.start_lesson(1)

    lesson = app.select_lesson(1)

    fake_inputs = [
        "Hello my name is Ana",
        "Nice to meet you",
        "How are you todey?",
    ]

    for index, segment in enumerate(lesson.segments):
        print(f"\nSegment {index + 1}")
        app.play_segment(segment)

        result = app.submit_answer(fake_inputs[index])

        print(f"Input: {fake_inputs[index]}")
        print(
            f"Similarity: {result['similarity']} | "
            f"Correct: {result['is_correct']}"
        )

        if index < len(lesson.segments) - 1:
            app.next_segment()

    final_result = app.finish_lesson()

    print("\nFinal Result:")
    for key, value in final_result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    demo()
