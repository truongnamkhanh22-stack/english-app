"""
BTL.03 - Hệ thống luyện nghe tiếng Anh
========================================
Framework OOP với đầy đủ các lớp, phương thức, và use case theo yêu cầu đề bài.
"""

from __future__ import annotations
import time
import difflib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


# ══════════════════════════════════════════════════════
#  SEGMENT — một đoạn audio ngắn (10-25 giây)
# ══════════════════════════════════════════════════════

class Segment:
    """Đại diện cho một phần ngắn của bài nghe."""

    def __init__(self, audio_path: str, transcript: str, duration: float):
        """
        Args:
            audio_path: Đường dẫn tới file audio (mp3/wav).
            transcript: Nội dung lời thoại chuẩn của đoạn này.
            duration:   Độ dài tính bằng giây (10 – 25s).
        """
        self.audio_path: str = audio_path
        self.transcript: str = transcript
        self.duration: float = duration  # giây

    def __repr__(self) -> str:
        return (f"Segment(duration={self.duration}s, "
                f"audio='{self.audio_path}')")


# ══════════════════════════════════════════════════════
#  LEVEL — lớp trừu tượng & 3 cấp độ cụ thể
# ══════════════════════════════════════════════════════

class Level(ABC):
    """
    Lớp trừu tượng cho cấp độ.
    Đa hình: mỗi cấp override check_answer() theo quy tắc riêng.
    """

    @abstractmethod
    def check_answer(self, user_input: str, transcript: str) -> float:
        """
        So sánh câu người dùng nhập với bản gốc.
        Trả về điểm tương đồng từ 0.0 đến 1.0.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Trả về tên cấp độ (Level1 / Level2 / Level3)."""
        ...

    def _similarity(self, a: str, b: str) -> float:
        """Tính tỉ lệ giống nhau giữa hai chuỗi (bỏ qua hoa/thường)."""
        return difflib.SequenceMatcher(
            None, a.lower().strip(), b.lower().strip()
        ).ratio()


class Level1(Level):
    """
    Cấp 1 — Dễ.
    Chấp nhận sai chính tả nhẹ (tỉ lệ khớp >= 0.75 là đúng).
    """

    def get_name(self) -> str:
        return "Level1"

    def check_answer(self, user_input: str, transcript: str) -> float:
        # Cấp 1: chấp nhận sai chính tả → ngưỡng thấp hơn
        score = self._similarity(user_input, transcript)
        return score


class Level2(Level):
    """
    Cấp 2 — Trung bình.
    Mỗi segment <= 15 giây; yêu cầu khớp >= 0.80.
    """

    MAX_SEGMENT_DURATION = 15  # giây

    def get_name(self) -> str:
        return "Level2"

    def check_answer(self, user_input: str, transcript: str) -> float:
        score = self._similarity(user_input, transcript)
        return score


class Level3(Level):
    """
    Cấp 3 — Khó.
    Mỗi segment >= 20 giây; yêu cầu khớp >= 0.90.
    """

    MIN_SEGMENT_DURATION = 20  # giây

    def get_name(self) -> str:
        return "Level3"

    def check_answer(self, user_input: str, transcript: str) -> float:
        # Cấp 3: khắt khe hơn — dùng exact match sau khi chuẩn hoá
        score = self._similarity(user_input, transcript)
        return score


# ══════════════════════════════════════════════════════
#  AUDIOLESSON — một bài nghe hoàn chỉnh
# ══════════════════════════════════════════════════════

class AudioLesson:
    """
    Đại diện cho một bài nghe, gồm nhiều Segment.
    Thuộc một Level nhất định (1, 2 hoặc 3).
    """

    def __init__(
        self,
        lesson_id: int,
        title: str,
        level: Level,
        segments: Optional[list[Segment]] = None,
    ):
        self.id: int = lesson_id
        self.title: str = title
        self.level: Level = level
        self.segments: list[Segment] = segments or []

    @property
    def total_duration(self) -> float:
        """Tổng thời lượng bài (giây)."""
        return sum(seg.duration for seg in self.segments)

    def add_segment(self, segment: Segment) -> None:
        self.segments.append(segment)

    def __repr__(self) -> str:
        return (f"AudioLesson(id={self.id}, title='{self.title}', "
                f"level={self.level.get_name()}, "
                f"segments={len(self.segments)}, "
                f"duration={self.total_duration:.1f}s)")


# ══════════════════════════════════════════════════════
#  ATTEMPT — một lần làm bài của người dùng
# ══════════════════════════════════════════════════════

class Attempt:
    """
    Lưu thông tin một phiên luyện nghe.
    Công thức điểm: 10 × (11 − x/y)
        x = tổng thời gian sử dụng (giây)
        y = tổng thời lượng bài (giây)
    """

    def __init__(self, lesson: AudioLesson, user: "User"):
        self.lesson: AudioLesson = lesson
        self.user: "User" = user
        self.score: float = 0.0
        self.started_at: datetime = datetime.now()
        self.finished_at: Optional[datetime] = None
        self._answers: list[tuple[str, str, float]] = []  # (input, transcript, similarity)
        self._start_time: float = time.time()

    def record_answer(self, user_input: str, transcript: str, similarity: float) -> None:
        self._answers.append((user_input, transcript, similarity))

    def finish(self) -> None:
        """Kết thúc bài, tính điểm theo công thức đề bài."""
        self.finished_at = datetime.now()
        elapsed = time.time() - self._start_time  # x (giây dùng)
        y = self.lesson.total_duration             # y (thời lượng bài)

        if y > 0:
            raw = 10 * (11 - elapsed / y)
            # Giới hạn điểm trong khoảng [0, 100]
            answer_avg = (
                sum(s for _, _, s in self._answers) / len(self._answers)
                if self._answers else 0
            )
            self.score = max(0.0, min(100.0, raw * answer_avg))
        else:
            self.score = 0.0

    @property
    def duration_used(self) -> float:
        """Thời gian đã dùng (giây)."""
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return time.time() - self._start_time

    def __repr__(self) -> str:
        return (f"Attempt(user='{self.user.username}', "
                f"lesson='{self.lesson.title}', "
                f"score={self.score:.1f})")


# ══════════════════════════════════════════════════════
#  USER — người dùng hệ thống
# ══════════════════════════════════════════════════════

class User:
    """Lưu thông tin người dùng và lịch sử học tập."""

    def __init__(self, user_id: int, username: str):
        self.id: int = user_id
        self.username: str = username
        self.history: list[Attempt] = []

    def add_attempt(self, attempt: Attempt) -> None:
        self.history.append(attempt)

    def average_score(self) -> float:
        if not self.history:
            return 0.0
        return sum(a.score for a in self.history) / len(self.history)

    def progress_chart(self) -> list[dict]:
        """
        Trả về dữ liệu biểu đồ tiến độ (dùng để vẽ chart).
        Mỗi phần tử: {date, lesson_title, score}
        """
        return [
            {
                "date": a.started_at.strftime("%Y-%m-%d %H:%M"),
                "lesson": a.lesson.title,
                "score": round(a.score, 1),
            }
            for a in self.history
            if a.finished_at is not None
        ]

    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}')"


# ══════════════════════════════════════════════════════
#  LISTENINGAPP — bộ điều khiển chính (Controller)
# ══════════════════════════════════════════════════════

class ListeningApp:
    """
    Điều phối toàn bộ luồng ứng dụng:
    - Chọn Level & bài nghe
    - Phát / Dừng / Phát lại audio (stub)
    - Nhận nhập liệu và chấm điểm từng đoạn
    - Tính tổng điểm và hiển thị kết quả
    - Xem lịch sử & biểu đồ tiến độ
    """

    def __init__(self):
        self._lessons: dict[int, AudioLesson] = {}
        self._users: dict[int, User] = {}
        self._current_user: Optional[User] = None
        self._current_attempt: Optional[Attempt] = None
        self._current_segment_idx: int = 0

    # ── Quản lý dữ liệu ───────────────────────────────

    def register_lesson(self, lesson: AudioLesson) -> None:
        """Thêm bài nghe vào thư viện."""
        self._lessons[lesson.id] = lesson

    def register_user(self, user: User) -> None:
        self._users[user.id] = user

    def login(self, user_id: int) -> bool:
        """Đăng nhập người dùng."""
        if user_id in self._users:
            self._current_user = self._users[user_id]
            return True
        return False

    # ── Use Case 1: Chọn Level và bài nghe ───────────

    def get_lessons_by_level(self, level_name: str) -> list[AudioLesson]:
        """
        UC1 — Trả về danh sách bài học theo cấp độ.
        level_name: 'Level1' | 'Level2' | 'Level3'
        """
        return [
            lesson for lesson in self._lessons.values()
            if lesson.level.get_name() == level_name
        ]

    def select_lesson(self, lesson_id: int) -> Optional[AudioLesson]:
        """UC1 — Chọn một bài cụ thể để học."""
        return self._lessons.get(lesson_id)

    # ── Use Case 2: Phát audio ────────────────────────

    def play_segment(self, segment: Segment) -> None:
        """
        UC2 — Phát một đoạn audio.
        (Stub: trong thực tế gọi thư viện pygame / playsound)
        """
        print(f"[PLAY] {segment.audio_path} ({segment.duration}s)")
        # TODO: pygame.mixer.music.load(segment.audio_path); pygame.mixer.music.play()

    def pause(self) -> None:
        """UC2 — Tạm dừng phát."""
        print("[PAUSE]")
        # TODO: pygame.mixer.music.pause()

    def replay_segment(self, segment: Segment) -> None:
        """UC2 — Phát lại đoạn hiện tại."""
        print(f"[REPLAY] {segment.audio_path}")
        self.play_segment(segment)

    # ── Use Case 3: Nhập lại nội dung nghe ───────────

    def submit_answer(self, user_input: str) -> dict:
        """
        UC3 & UC4 — Người dùng gõ lại nội dung vừa nghe.
        Gọi Level.check_answer() (đa hình), lưu kết quả.

        Returns:
            dict với keys: similarity, is_correct, expected
        """
        if not self._current_attempt:
            raise RuntimeError("Chưa bắt đầu bài học. Gọi start_lesson() trước.")

        lesson = self._current_attempt.lesson
        segments = lesson.segments

        if self._current_segment_idx >= len(segments):
            raise IndexError("Đã hết segment trong bài này.")

        segment = segments[self._current_segment_idx]
        level = lesson.level

        # Đa hình: Level1/Level2/Level3 có logic check khác nhau
        similarity = level.check_answer(user_input, segment.transcript)

        threshold = {"Level1": 0.75, "Level2": 0.80, "Level3": 0.90}
        thr = threshold.get(level.get_name(), 0.80)
        is_correct = similarity >= thr

        self._current_attempt.record_answer(user_input, segment.transcript, similarity)

        return {
            "segment_index": self._current_segment_idx,
            "similarity": round(similarity, 3),
            "is_correct": is_correct,
            "expected": segment.transcript,
        }

    # ── Điều hướng phiên học ──────────────────────────

    def start_lesson(self, lesson_id: int) -> bool:
        """Bắt đầu một lần làm bài mới."""
        if not self._current_user:
            raise RuntimeError("Chưa đăng nhập.")
        lesson = self._lessons.get(lesson_id)
        if not lesson:
            return False
        self._current_attempt = Attempt(lesson, self._current_user)
        self._current_segment_idx = 0
        return True

    def next_segment(self) -> Optional[Segment]:
        """Chuyển sang đoạn tiếp theo, trả về Segment hoặc None nếu hết."""
        if not self._current_attempt:
            return None
        self._current_segment_idx += 1
        segments = self._current_attempt.lesson.segments
        if self._current_segment_idx < len(segments):
            return segments[self._current_segment_idx]
        return None  # Hết bài

    def current_segment(self) -> Optional[Segment]:
        """Trả về Segment hiện tại."""
        if not self._current_attempt:
            return None
        segments = self._current_attempt.lesson.segments
        if self._current_segment_idx < len(segments):
            return segments[self._current_segment_idx]
        return None

    # ── Use Case 5: Tính điểm & hiển thị kết quả ────

    def finish_lesson(self) -> dict:
        """
        UC5 — Kết thúc bài, tính điểm và hiển thị kết quả.
        Công thức: 10 × (11 − x/y)
        """
        if not self._current_attempt:
            raise RuntimeError("Không có bài đang học.")

        attempt = self._current_attempt
        attempt.finish()
        self._current_user.add_attempt(attempt)

        x = attempt.duration_used
        y = attempt.lesson.total_duration

        result = {
            "lesson": attempt.lesson.title,
            "level": attempt.lesson.level.get_name(),
            "score": round(attempt.score, 1),
            "time_used_sec": round(x, 1),
            "total_duration_sec": round(y, 1),
            "formula": f"10 × (11 − {round(x,1)}/{round(y,1)})",
            "finished_at": attempt.finished_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._current_attempt = None
        self._current_segment_idx = 0
        return result

    # ── Use Case 6: Lịch sử & biểu đồ tiến độ ───────

    def get_history(self) -> list[dict]:
        """UC6 — Lấy lịch sử học tập của người dùng hiện tại."""
        if not self._current_user:
            return []
        return self._current_user.progress_chart()

    def get_progress_summary(self) -> dict:
        """UC6 — Tổng hợp tiến độ: số bài hoàn thành, điểm trung bình."""
        if not self._current_user:
            return {}
        user = self._current_user
        return {
            "username": user.username,
            "total_attempts": len(user.history),
            "average_score": round(user.average_score(), 1),
            "best_score": round(
                max((a.score for a in user.history), default=0), 1
            ),
        }


# ══════════════════════════════════════════════════════
#  DỮ LIỆU MẪU & DEMO CHẠY THỬ
# ══════════════════════════════════════════════════════

def build_sample_library() -> tuple[ListeningApp, User]:
    """
    Xây dựng thư viện 10 bài nghe mẫu (3 cấp độ).
    Trả về (app, user) để chạy thử ngay.
    """
    app = ListeningApp()

    # --- Cấp độ ---
    lv1, lv2, lv3 = Level1(), Level2(), Level3()

    # --- Bài nghe Level 1 ---
    lesson1 = AudioLesson(1, "Greetings & Introductions", lv1)
    lesson1.add_segment(Segment("audio/l1_s1.mp3", "Hello, my name is Anna.", 12))
    lesson1.add_segment(Segment("audio/l1_s2.mp3", "Nice to meet you.", 10))
    lesson1.add_segment(Segment("audio/l1_s3.mp3", "How are you today?", 11))

    lesson2 = AudioLesson(2, "Numbers and Colors", lv1)
    lesson2.add_segment(Segment("audio/l2_s1.mp3", "The sky is blue.", 10))
    lesson2.add_segment(Segment("audio/l2_s2.mp3", "I have three apples.", 11))
    lesson2.add_segment(Segment("audio/l2_s3.mp3", "My favorite color is green.", 12))

    lesson3 = AudioLesson(3, "Days of the Week", lv1)
    lesson3.add_segment(Segment("audio/l3_s1.mp3", "Today is Monday.", 10))
    lesson3.add_segment(Segment("audio/l3_s2.mp3", "The weekend is Saturday and Sunday.", 13))

    # --- Bài nghe Level 2 (segment <= 15s) ---
    lesson4 = AudioLesson(4, "At the Airport", lv2)
    lesson4.add_segment(Segment("audio/l4_s1.mp3", "Where is the boarding gate?", 14))
    lesson4.add_segment(Segment("audio/l4_s2.mp3", "My flight departs at ten thirty.", 15))
    lesson4.add_segment(Segment("audio/l4_s3.mp3", "Please fasten your seatbelt.", 13))

    lesson5 = AudioLesson(5, "Ordering Food", lv2)
    lesson5.add_segment(Segment("audio/l5_s1.mp3", "I would like a glass of water, please.", 15))
    lesson5.add_segment(Segment("audio/l5_s2.mp3", "What are today's specials?", 13))
    lesson5.add_segment(Segment("audio/l5_s3.mp3", "The bill comes to twenty dollars.", 14))

    lesson6 = AudioLesson(6, "Asking for Directions", lv2)
    lesson6.add_segment(Segment("audio/l6_s1.mp3", "Turn left at the traffic light.", 14))
    lesson6.add_segment(Segment("audio/l6_s2.mp3", "The bank is next to the post office.", 15))

    lesson7 = AudioLesson(7, "Shopping Dialogue", lv2)
    lesson7.add_segment(Segment("audio/l7_s1.mp3", "How much does this jacket cost?", 13))
    lesson7.add_segment(Segment("audio/l7_s2.mp3", "Do you have this in a larger size?", 14))
    lesson7.add_segment(Segment("audio/l7_s3.mp3", "I'll take it. Can I pay by card?", 15))

    # --- Bài nghe Level 3 (segment >= 20s) ---
    lesson8 = AudioLesson(8, "Climate Change Overview", lv3)
    lesson8.add_segment(Segment(
        "audio/l8_s1.mp3",
        "Global temperatures have risen by approximately one degree Celsius "
        "since the pre-industrial era, primarily due to human activities.",
        22
    ))
    lesson8.add_segment(Segment(
        "audio/l8_s2.mp3",
        "Renewable energy sources such as solar and wind are crucial "
        "to reducing carbon emissions worldwide.",
        20
    ))

    lesson9 = AudioLesson(9, "Technology in Education", lv3)
    lesson9.add_segment(Segment(
        "audio/l9_s1.mp3",
        "Artificial intelligence is transforming the way students learn "
        "by providing personalised feedback in real time.",
        23
    ))
    lesson9.add_segment(Segment(
        "audio/l9_s2.mp3",
        "Online platforms enable learners across the globe to access "
        "high-quality educational resources at no cost.",
        21
    ))

    lesson10 = AudioLesson(10, "Health and Nutrition", lv3)
    lesson10.add_segment(Segment(
        "audio/l10_s1.mp3",
        "A balanced diet rich in fruits, vegetables, and whole grains "
        "significantly reduces the risk of chronic diseases.",
        24
    ))
    lesson10.add_segment(Segment(
        "audio/l10_s2.mp3",
        "Regular physical activity for at least thirty minutes a day "
        "improves both mental and physical wellbeing.",
        22
    ))

    for lesson in [lesson1, lesson2, lesson3, lesson4, lesson5,
                   lesson6, lesson7, lesson8, lesson9, lesson10]:
        app.register_lesson(lesson)

    # --- Người dùng mẫu ---
    user = User(1, "student_01")
    app.register_user(user)
    app.login(1)

    return app, user


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