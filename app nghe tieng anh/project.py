from __future__ import annotations

import difflib
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class Segment:
    def __init__(self, audio_path: str, transcript: str, duration: float):
        self.audio_path = audio_path
        self.transcript = transcript
        self.duration = duration

    def __repr__(self) -> str:
        return f"Segment(duration={self.duration}s, audio='{self.audio_path}')"


class Level(ABC):
    @abstractmethod
    def check_answer(self, user_input: str, transcript: str) -> float:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def _similarity(self, a: str, b: str) -> float:
        return difflib.SequenceMatcher(
            None,
            a.lower().strip(),
            b.lower().strip(),
        ).ratio()


class Level1(Level):
    def get_name(self) -> str:
        return "Level1"

    def check_answer(self, user_input: str, transcript: str) -> float:
        return self._similarity(user_input, transcript)


class Level2(Level):
    MAX_SEGMENT_DURATION = 15

    def get_name(self) -> str:
        return "Level2"

    def check_answer(self, user_input: str, transcript: str) -> float:
        return self._similarity(user_input, transcript)


class Level3(Level):
    MIN_SEGMENT_DURATION = 20

    def get_name(self) -> str:
        return "Level3"

    def check_answer(self, user_input: str, transcript: str) -> float:
        return self._similarity(user_input, transcript)


class AudioLesson:
    def __init__(
        self,
        lesson_id: int,
        title: str,
        level: Level,
        segments: Optional[list[Segment]] = None,
    ):
        self.id = lesson_id
        self.title = title
        self.level = level
        self.segments = segments or []

    @property
    def total_duration(self) -> float:
        return sum(segment.duration for segment in self.segments)

    def add_segment(self, segment: Segment) -> None:
        self.segments.append(segment)

    def __repr__(self) -> str:
        return (
            f"AudioLesson(id={self.id}, title='{self.title}', "
            f"level={self.level.get_name()}, "
            f"segments={len(self.segments)}, "
            f"duration={self.total_duration:.1f}s)"
        )


class Attempt:
    def __init__(self, lesson: AudioLesson, user: "User"):
        self.lesson = lesson
        self.user = user
        self.score = 0.0
        self.started_at = datetime.now()
        self.finished_at: Optional[datetime] = None
        self._answers: list[tuple[str, str, float]] = []
        self._start_time = time.time()

    def record_answer(
        self,
        user_input: str,
        transcript: str,
        similarity: float,
    ) -> None:
        self._answers.append((user_input, transcript, similarity))

    def finish(self) -> None:
        self.finished_at = datetime.now()

        elapsed = time.time() - self._start_time
        total_duration = self.lesson.total_duration

        if total_duration <= 0:
            self.score = 0.0
            return

        raw_score = 10 * (11 - elapsed / total_duration)

        answer_average = (
            sum(score for _, _, score in self._answers) / len(self._answers)
            if self._answers
            else 0
        )

        self.score = max(0.0, min(100.0, raw_score * answer_average))

    @property
    def duration_used(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()

        return time.time() - self._start_time

    def __repr__(self) -> str:
        return (
            f"Attempt(user='{self.user.username}', "
            f"lesson='{self.lesson.title}', "
            f"score={self.score:.1f})"
        )


class User:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username
        self.history: list[Attempt] = []

    def add_attempt(self, attempt: Attempt) -> None:
        self.history.append(attempt)

    def average_score(self) -> float:
        if not self.history:
            return 0.0

        return sum(attempt.score for attempt in self.history) / len(self.history)

    def progress_chart(self) -> list[dict]:
        return [
            {
                "date": attempt.started_at.strftime("%Y-%m-%d %H:%M"),
                "lesson": attempt.lesson.title,
                "score": round(attempt.score, 1),
            }
            for attempt in self.history
            if attempt.finished_at is not None
        ]

    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}')"


class ListeningApp:
    def __init__(self):
        self._lessons: dict[int, AudioLesson] = {}
        self._users: dict[int, User] = {}
        self._current_user: Optional[User] = None
        self._current_attempt: Optional[Attempt] = None
        self._current_segment_idx = 0

    def register_lesson(self, lesson: AudioLesson) -> None:
        self._lessons[lesson.id] = lesson

    def register_user(self, user: User) -> None:
        self._users[user.id] = user

    def login(self, user_id: int) -> bool:
        if user_id not in self._users:
            return False

        self._current_user = self._users[user_id]
        return True

    def get_lessons_by_level(self, level_name: str) -> list[AudioLesson]:
        return [
            lesson
            for lesson in self._lessons.values()
            if lesson.level.get_name() == level_name
        ]

    def select_lesson(self, lesson_id: int) -> Optional[AudioLesson]:
        return self._lessons.get(lesson_id)

    def play_segment(self, segment: Segment) -> None:
        print(f"[PLAY] {segment.audio_path} ({segment.duration}s)")

    def pause(self) -> None:
        print("[PAUSE]")

    def replay_segment(self, segment: Segment) -> None:
        print(f"[REPLAY] {segment.audio_path}")
        self.play_segment(segment)

    def submit_answer(self, user_input: str) -> dict:
        if not self._current_attempt:
            raise RuntimeError("Chưa bắt đầu bài học.")

        lesson = self._current_attempt.lesson
        segments = lesson.segments

        if self._current_segment_idx >= len(segments):
            raise IndexError("Đã hết segment trong bài.")

        segment = segments[self._current_segment_idx]
        level = lesson.level

        similarity = level.check_answer(user_input, segment.transcript)

        thresholds = {
            "Level1": 0.75,
            "Level2": 0.80,
            "Level3": 0.90,
        }

        is_correct = similarity >= thresholds.get(level.get_name(), 0.80)

        self._current_attempt.record_answer(
            user_input,
            segment.transcript,
            similarity,
        )

        return {
            "segment_index": self._current_segment_idx,
            "similarity": round(similarity, 3),
            "is_correct": is_correct,
            "expected": segment.transcript,
        }

    def start_lesson(self, lesson_id: int) -> bool:
        if not self._current_user:
            raise RuntimeError("Chưa đăng nhập.")

        lesson = self._lessons.get(lesson_id)

        if not lesson:
            return False

        self._current_attempt = Attempt(lesson, self._current_user)
        self._current_segment_idx = 0

        return True

    def next_segment(self) -> Optional[Segment]:
        if not self._current_attempt:
            return None

        self._current_segment_idx += 1

        segments = self._current_attempt.lesson.segments

        if self._current_segment_idx < len(segments):
            return segments[self._current_segment_idx]

        return None

    def current_segment(self) -> Optional[Segment]:
        if not self._current_attempt:
            return None

        segments = self._current_attempt.lesson.segments

        if self._current_segment_idx < len(segments):
            return segments[self._current_segment_idx]

        return None

    def finish_lesson(self) -> dict:
        if not self._current_attempt:
            raise RuntimeError("Không có bài đang học.")

        attempt = self._current_attempt

        attempt.finish()
        self._current_user.add_attempt(attempt)

        result = {
            "lesson": attempt.lesson.title,
            "level": attempt.lesson.level.get_name(),
            "score": round(attempt.score, 1),
            "time_used_sec": round(attempt.duration_used, 1),
            "total_duration_sec": round(
                attempt.lesson.total_duration,
                1,
            ),
            "finished_at": attempt.finished_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        self._current_attempt = None
        self._current_segment_idx = 0

        return result

    def get_history(self) -> list[dict]:
        if not self._current_user:
            return []

        return self._current_user.progress_chart()

    def get_progress_summary(self) -> dict:
        if not self._current_user:
            return {}

        user = self._current_user

        return {
            "username": user.username,
            "total_attempts": len(user.history),
            "average_score": round(user.average_score(), 1),
            "best_score": round(
                max((attempt.score for attempt in user.history), default=0),
                1,
            ),
        }


def build_sample_library() -> tuple[ListeningApp, User]:
    app = ListeningApp()

    lv1 = Level1()
    lv2 = Level2()
    lv3 = Level3()

    lesson1 = AudioLesson(1, "Greetings & Introductions", lv1)
    lesson1.add_segment(
        Segment("audio/l1_s1.mp3", "Hello, my name is Anna.", 12)
    )
    lesson1.add_segment(
        Segment("audio/l1_s2.mp3", "Nice to meet you.", 10)
    )
    lesson1.add_segment(
        Segment("audio/l1_s3.mp3", "How are you today?", 11)
    )

    lesson2 = AudioLesson(2, "Numbers and Colors", lv1)
    lesson2.add_segment(
        Segment("audio/l2_s1.mp3", "The sky is blue.", 10)
    )
    lesson2.add_segment(
        Segment("audio/l2_s2.mp3", "I have three apples.", 11)
    )
    lesson2.add_segment(
        Segment(
            "audio/l2_s3.mp3",
            "My favorite color is green.",
            12,
        )
    )

    lesson3 = AudioLesson(3, "Days of the Week", lv1)
    lesson3.add_segment(
        Segment("audio/l3_s1.mp3", "Today is Monday.", 10)
    )
    lesson3.add_segment(
        Segment(
            "audio/l3_s2.mp3",
            "The weekend is Saturday and Sunday.",
            13,
        )
    )

    lesson4 = AudioLesson(4, "At the Airport", lv2)
    lesson4.add_segment(
        Segment("audio/l4_s1.mp3", "Where is the boarding gate?", 14)
    )
    lesson4.add_segment(
        Segment("audio/l4_s2.mp3", "My flight departs at ten thirty.", 15)
    )
    lesson4.add_segment(
        Segment("audio/l4_s3.mp3", "Please fasten your seatbelt.", 13)
    )

    lesson5 = AudioLesson(5, "Ordering Food", lv2)
    lesson5.add_segment(
        Segment("audio/l5_s1.mp3", "I would like a glass of water, please.", 15)
    )
    lesson5.add_segment(
        Segment("audio/l5_s2.mp3", "What are today's specials?", 13)
    )
    lesson5.add_segment(
        Segment("audio/l5_s3.mp3", "The bill comes to twenty dollars.", 14)
    )

    lesson6 = AudioLesson(6, "Asking for Directions", lv2)
    lesson6.add_segment(
        Segment("audio/l6_s1.mp3", "Turn left at the traffic light.", 14)
    )
    lesson6.add_segment(
        Segment("audio/l6_s2.mp3", "The bank is next to the post office.", 15)
    )
    lesson6.add_segment(
        Segment("audio/l6_s3.mp3", "Go straight ahead for two blocks.", 13)
    )

    lesson7 = AudioLesson(7, "Climate Change Overview", lv3)
    lesson7.add_segment(
        Segment(
            "audio/l7_s1.mp3",
            "Global temperatures have risen by approximately one degree Celsius "
            "since the pre-industrial era, primarily due to human activities.",
            22,
        )
    )
    lesson7.add_segment(
        Segment(
            "audio/l7_s2.mp3",
            "Renewable energy sources such as solar and wind are crucial "
            "to reducing carbon emissions worldwide.",
            20,
        )
    )
    lesson7.add_segment(
        Segment(
            "audio/l7_s3.mp3",
            "Governments and individuals must work together to limit "
            "the effects of climate change for future generations.",
            21,
        )
    )

    lesson8 = AudioLesson(8, "Technology in Education", lv3)
    lesson8.add_segment(
        Segment(
            "audio/l8_s1.mp3",
            "Artificial intelligence is transforming the way students learn "
            "by providing personalised feedback in real time.",
            23,
        )
    )
    lesson8.add_segment(
        Segment(
            "audio/l8_s2.mp3",
            "Online platforms enable learners across the globe to access "
            "high-quality educational resources at no cost.",
            21,
        )
    )
    lesson8.add_segment(
        Segment(
            "audio/l8_s3.mp3",
            "Critical thinking and digital literacy are essential skills "
            "for students in the twenty-first century.",
            20,
        )
    )

    for lesson in [lesson1, lesson2, lesson3, lesson4, lesson5,
                   lesson6, lesson7, lesson8]:
        app.register_lesson(lesson)

    user = User(1, "student_01")

    app.register_user(user)
    app.login(1)

    return app, user
