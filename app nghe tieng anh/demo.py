from project import build_sample_library


def demo():
    print("=" * 60)
    print("English Listening App Demo")
    print("=" * 60)

    app, _ = build_sample_library()

    for level_name in ("Level1", "Level2", "Level3"):
        print(f"\n{level_name} Lessons:")
        for lesson in app.get_lessons_by_level(level_name):
            print(f"  {lesson}")

    # ── Bắt đầu bài học ──────────────────────────────────────
    print("\n" + "-" * 60)
    print("Starting lesson 1: Greetings & Introductions")
    print("-" * 60)
    app.start_lesson(1)
    lesson = app.select_lesson(1)

    fake_inputs = [
        "Hello my name is Ana",   # Segment 1: nghe 1 lần, nhập luôn
        "Nice to meet you",       # Segment 2: nghe rồi Pause, nhập sau
        "How are you todey?",     # Segment 3: nghe không rõ, Replay rồi nhập
    ]

    for index, segment in enumerate(lesson.segments):
        print(f"\n{'─' * 40}")
        print(f"Segment {index + 1} / {len(lesson.segments)}")
        print(f"{'─' * 40}")

        if index == 0:
            print("[Action] User plays the segment.")
            app.play_segment(segment)

        elif index == 1:
            print("[Action] User plays the segment.")
            app.play_segment(segment)
            print("[Action] User pauses to think.")
            app.pause()
            print("[Action] User resumes and finishes listening.")
            app.play_segment(segment)

        elif index == 2:
            print("[Action] User plays the segment.")
            app.play_segment(segment)
            print("[Action] Audio was unclear — user replays.")
            app.replay_segment(segment)

        result = app.submit_answer(fake_inputs[index])
        print(f"[Input]  \"{fake_inputs[index]}\"")
        print(f"[Expect] \"{result['expected']}\"")
        print(
            f"[Score]  Similarity: {result['similarity']} | "
            f"Correct: {result['is_correct']}"
        )

        if index < len(lesson.segments) - 1:
            app.next_segment()
            
    print("\n" + "=" * 60)
    print("Final Result")
    print("=" * 60)
    final_result = app.finish_lesson()
    for key, value in final_result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
