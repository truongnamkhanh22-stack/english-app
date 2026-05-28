from project import build_sample_library
def demo():
    """Chạy thử các use case chính."""
    print("=" * 60)
    print("  BTL.03 — Hệ thống luyện nghe tiếng Anh (Demo)")
    print("=" * 60)

    app, user = build_sample_library()

    # UC1: Xem danh sách bài theo cấp độ
    print("\n[UC1] Bài Level1:")
    for lesson in app.get_lessons_by_level("Level1"):
        print(f"  {lesson}")

    print("\n[UC1] Bài Level2:")
    for lesson in app.get_lessons_by_level("Level2"):
        print(f"  {lesson}")

    print("\n[UC1] Bài Level3:")
    for lesson in app.get_lessons_by_level("Level3"):
        print(f"  {lesson}")

    # UC2 + UC3 + UC4 + UC5: Làm một bài hoàn chỉnh
    print("\n[UC2-5] Bắt đầu bài 1 — 'Greetings & Introductions'")
    app.start_lesson(1)

    lesson = app.select_lesson(1)
    for i, segment in enumerate(lesson.segments):
        print(f"\n  ▶ Segment {i+1}: phát '{segment.audio_path}'")
        app.play_segment(segment)

        # Giả lập người dùng nhập (có lỗi chính tả nhỏ)
        fake_inputs = [
            "Hello my name is Ana",   # gần đúng
            "Nice to meet you",       # đúng hoàn toàn
            "How are you todey?",     # lỗi nhỏ
        ]
        result = app.submit_answer(fake_inputs[i])
        print(f"  ✎ Nhập: '{fake_inputs[i]}'")
        print(f"  ✔ Kết quả: tương đồng={result['similarity']}, "
              f"đúng={result['is_correct']}")

        if i < len(lesson.segments) - 1:
            app.next_segment()

    # UC5: Kết thúc & tính điểm
    final = app.finish_lesson()
    print("\n[UC5] Kết quả cuối bài:")
    for k, v in final.items():
        print(f"  {k}: {v}")

    # UC6: Lịch sử & tiến độ
    print("\n[UC6] Lịch sử học tập:")
    for record in app.get_history():
        print(f"  {record}")

    print("\n[UC6] Tổng hợp tiến độ:")
    summary = app.get_progress_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n✅ Demo hoàn tất.")


if __name__ == "__main__":
    demo()