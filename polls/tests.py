import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


def create_question(question_text, days: int):
    """
        Create a question with the given `question_text` and published the
        given number of `days` offset to now (negative for questions published
        in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, publication_date=time)


class QuestionModelTest(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose publication_date is in the future
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(publication_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose publication_date is older than 1 day
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(publication_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose publication_date is within the last day
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(publication_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


class QuestionIndexViewTest(TestCase):
    def test_no_questions(self):
        """
            If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There is no questions.")
        
    def test_past_questions(self):
        """
            Questions with a pub_date in the past are displayed on the index page.
        """
        question = create_question("Past question", -29)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_future_question(self):
        """
            Questions with a pub_date in the future aren't displayed on the index page.
        """
        create_question("Past question", 29)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "There is no questions.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_and_past_question(self):
        """
            Even if both past and future questions exist, only past questions are displayed.
        """
        question = create_question("Past question", -29)
        create_question("Past question", 29)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_two_past_question(self):
        """
            The questions index page may display multiple questions.
        """
        question1 = create_question("Past question", -29)
        question2 = create_question("Past question", -29)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question1, question2])

    def test_question_with_choice(self):
        """
            The questions with choices are displayed.
        """
        question = create_question("question", days=0)
        Choice.objects.create(question=question, choice_text="choice")
        response = self.client.get(reverse("polls:index"))
        self.assertIn(question.question_text, response.content.decode())

    def test_question_with_no_choice(self):
        """
            The questions without choices are not displayed.
        """
        question = create_question("question", days=0)
        response = self.client.get(reverse("polls:index"))
        print(response.content.decode())
        self.assertNotIn(question.question_text, response.content.decode())


class QuestionDetailViewTest(TestCase):
    def test_future_question(self):
        """
            The detail view of a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question("future question.", 29)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
           The detail view of a question with a pub_date in the past displays the question's text.
        """
        past_question = create_question("past question.", days=-23)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)