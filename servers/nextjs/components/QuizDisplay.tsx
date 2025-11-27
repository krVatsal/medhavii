"use client";
import React, { useState } from "react";
import { QuizData, QuizQuestion } from "@/lib/quiz-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, XCircle, Lightbulb } from "lucide-react";

interface QuizDisplayProps {
  quizData: QuizData;
  slideRange: string;
  difficulty: string;
  onClose: () => void;
}

const QuizDisplay: React.FC<QuizDisplayProps> = ({
  quizData,
  slideRange,
  difficulty,
  onClose,
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState<boolean[]>(
    new Array(quizData.quiz.length).fill(false)
  );
  const [isQuizComplete, setIsQuizComplete] = useState(false);

  const currentQuestion = quizData.quiz[currentQuestionIndex];
  const totalQuestions = quizData.quiz.length;

  const handleAnswerSelect = (answer: string) => {
    if (answeredQuestions[currentQuestionIndex]) return;
    
    setSelectedAnswer(answer);
    setShowExplanation(true);

    const isCorrect = answer === currentQuestion.correct_answer;
    if (isCorrect) {
      setScore(score + 1);
    }

    const newAnswered = [...answeredQuestions];
    newAnswered[currentQuestionIndex] = true;
    setAnsweredQuestions(newAnswered);
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } else {
      setIsQuizComplete(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    }
  };

  const handleRestart = () => {
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setShowExplanation(false);
    setScore(0);
    setAnsweredQuestions(new Array(totalQuestions).fill(false));
    setIsQuizComplete(false);
  };

  const getOptionLetter = (option: string): string => {
    return option.split(")")[0];
  };

  const isCorrect = selectedAnswer === currentQuestion?.correct_answer;

  if (isQuizComplete) {
    const percentage = Math.round((score / totalQuestions) * 100);
    return (
      <Card className="w-full max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle className="text-center text-2xl">Quiz Complete! 🎉</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center space-y-4">
            <div className="text-6xl font-bold text-red-600">
              {percentage}%
            </div>
            <p className="text-xl">
              You scored {score} out of {totalQuestions}
            </p>
            <div className="text-sm text-gray-600">
              <p>Slide Range: {slideRange}</p>
              <p>Difficulty: {difficulty}</p>
            </div>
          </div>
          
          <div className="flex gap-3 justify-center">
            <Button onClick={handleRestart} variant="default">
              Restart Quiz
            </Button>
            <Button onClick={onClose} variant="outline">
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </CardTitle>
          <div className="text-sm space-x-4">
            <span className="text-gray-600">Score: {score}</span>
            <span className="text-gray-600 capitalize">Difficulty: {difficulty}</span>
          </div>
        </div>
        <p className="text-sm text-gray-500">Slide Range: {slideRange}</p>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="text-lg font-medium">{currentQuestion.question}</div>

        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => {
            const optionLetter = getOptionLetter(option);
            const isSelected = selectedAnswer === optionLetter;
            const isCorrectAnswer = optionLetter === currentQuestion.correct_answer;
            
            let buttonClass = "w-full text-left p-4 border-2 rounded-lg transition-all ";
            
            if (showExplanation) {
              if (isCorrectAnswer) {
                buttonClass += "border-green-500 bg-green-50";
              } else if (isSelected && !isCorrect) {
                buttonClass += "border-red-500 bg-red-50";
              } else {
                buttonClass += "border-gray-300";
              }
            } else {
              buttonClass += isSelected
                ? "border-red-500 bg-red-50"
                : "border-gray-300 hover:border-red-300 hover:bg-gray-50";
            }

            return (
              <button
                key={index}
                onClick={() => handleAnswerSelect(optionLetter)}
                disabled={answeredQuestions[currentQuestionIndex]}
                className={buttonClass}
              >
                <div className="flex items-center justify-between">
                  <span>{option}</span>
                  {showExplanation && isCorrectAnswer && (
                    <CheckCircle2 className="text-green-600 w-6 h-6" />
                  )}
                  {showExplanation && isSelected && !isCorrect && (
                    <XCircle className="text-red-600 w-6 h-6" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {showExplanation && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded">
            <div className="flex items-start gap-2">
              <Lightbulb className="text-red-600 w-5 h-5 mt-1 flex-shrink-0" />
              <div>
                <p className="font-semibold text-red-900 mb-1">Explanation:</p>
                <p className="text-red-800">{currentQuestion.explanation}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center pt-4">
          <Button
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            variant="outline"
          >
            Previous
          </Button>

          <div className="flex gap-2">
            {Array.from({ length: totalQuestions }).map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full ${
                  index === currentQuestionIndex
                    ? "bg-red-600"
                    : answeredQuestions[index]
                    ? "bg-rose-500"
                    : "bg-gray-300"
                }`}
              />
            ))}
          </div>

          <Button
            onClick={handleNext}
            disabled={!answeredQuestions[currentQuestionIndex]}
            variant="default"
          >
            {currentQuestionIndex === totalQuestions - 1 ? "Finish" : "Next"}
          </Button>
        </div>

        <div className="flex justify-center">
          <Button onClick={onClose} variant="ghost" size="sm">
            Close Quiz
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default QuizDisplay;
