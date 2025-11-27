"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Loader2, Brain } from "lucide-react";
import { generateQuiz, QuizResponse } from "@/lib/quiz-api";
import QuizDisplay from "./QuizDisplay";
import { toast } from "sonner";

interface GenerateQuizButtonProps {
  presentationId: string;
  currentSlide: number;
  totalSlides: number;
}

const GenerateQuizButton: React.FC<GenerateQuizButtonProps> = ({
  presentationId,
  currentSlide,
  totalSlides,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [quizResponse, setQuizResponse] = useState<QuizResponse | null>(null);
  const [showQuiz, setShowQuiz] = useState(false);

  // Form state
  const [slideStart, setSlideStart] = useState(currentSlide + 1);
  const [slideEnd, setSlideEnd] = useState(currentSlide + 1);
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await generateQuiz({
        presentation_id: presentationId,
        slide_start: slideStart,
        slide_end: slideEnd,
        num_questions: numQuestions,
        difficulty: difficulty,
      });

      if (response.success && response.quiz_data) {
        setQuizResponse(response);
        setShowQuiz(true);
        setIsOpen(false);
        toast.success("Quiz Generated!", {
          description: `Successfully generated ${response.num_questions} questions.`,
        });
      } else {
        toast.error("Quiz Generation Failed", {
          description: response.error || "Failed to generate quiz",
        });
      }
    } catch (error) {
      console.error("Error generating quiz:", error);
      toast.error("Error", {
        description: "Failed to generate quiz. Please try again.",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClose = () => {
    setShowQuiz(false);
    setQuizResponse(null);
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Brain className="w-4 h-4" />
            Generate Quiz
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Generate Quiz from Slides</DialogTitle>
            <DialogDescription>
              Create quiz questions based on your presentation slides
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="slide-start">Start Slide</Label>
                <Input
                  id="slide-start"
                  type="number"
                  min={1}
                  max={totalSlides}
                  value={slideStart}
                  onChange={(e) => setSlideStart(parseInt(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="slide-end">End Slide</Label>
                <Input
                  id="slide-end"
                  type="number"
                  min={slideStart}
                  max={totalSlides}
                  value={slideEnd}
                  onChange={(e) => setSlideEnd(parseInt(e.target.value))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="num-questions">Number of Questions</Label>
              <Select
                value={numQuestions.toString()}
                onValueChange={(value) => setNumQuestions(parseInt(value))}
              >
                <SelectTrigger id="num-questions">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[3, 5, 7, 10].map((num) => (
                    <SelectItem key={num} value={num.toString()}>
                      {num} questions
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="difficulty">Difficulty Level</Label>
              <Select
                value={difficulty}
                onValueChange={(value) =>
                  setDifficulty(value as "easy" | "medium" | "hard")
                }
              >
                <SelectTrigger id="difficulty">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="pt-2">
              <p className="text-sm text-gray-600">
                Quiz will be generated from slides {slideStart} to {slideEnd}
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || slideStart > slideEnd}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Quiz"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {showQuiz && quizResponse?.quiz_data && (
        <Dialog open={showQuiz} onOpenChange={setShowQuiz}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <QuizDisplay
              quizData={quizResponse.quiz_data}
              slideRange={quizResponse.slide_range}
              difficulty={quizResponse.difficulty}
              onClose={handleClose}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
};

export default GenerateQuizButton;
