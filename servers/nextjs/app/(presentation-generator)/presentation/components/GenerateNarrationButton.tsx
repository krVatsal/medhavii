/**
 * Button to generate and manage voice narration for presentations
 */

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Volume2, Loader2 } from "lucide-react";
import { NarrationApi } from "../../services/api/narration-api";
import { PresentationNarration } from "@/models/narration";
import { toast } from "sonner";

interface GenerateNarrationButtonProps {
  presentationId: string;
  onNarrationGenerated: (narration: PresentationNarration) => void;
}

const GenerateNarrationButton: React.FC<GenerateNarrationButtonProps> = ({
  presentationId,
  onNarrationGenerated,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [languageCode, setLanguageCode] = useState("hi");
  const [voiceGender, setVoiceGender] = useState<"male" | "female">("female");
  const [studentLevel, setStudentLevel] = useState<"beginner" | "intermediate" | "advanced">("intermediate");
  const [includeRegionalReferences, setIncludeRegionalReferences] = useState(true);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const narration = await NarrationApi.generatePresentationNarration({
        presentation_id: presentationId,
        language_code: languageCode,
        voice_gender: voiceGender,
        student_level: studentLevel,
        include_regional_references: includeRegionalReferences,
      });

      toast.success("Voice narration generated successfully!", {
        description: `Generated ${narration.slides.length} slide narrations in ${Math.round(narration.total_duration_seconds / 60)} minutes`,
      });

      onNarrationGenerated(narration);
      setOpen(false);
    } catch (error: any) {
      toast.error("Failed to generate narration", {
        description: error.message || "Please try again",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Volume2 className="h-4 w-4" />
          Generate Voice Narration
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Generate Voice Narration</DialogTitle>
          <DialogDescription>
            Create AI-powered teaching-style voice narration for your presentation using Bhashini.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Language Selection */}
          <div className="grid gap-2">
            <Label htmlFor="language">Language</Label>
            <Select value={languageCode} onValueChange={setLanguageCode}>
              <SelectTrigger id="language">
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hi">Hindi (हिंदी)</SelectItem>
                <SelectItem value="bn">Bengali (বাংলা)</SelectItem>
                <SelectItem value="ta">Tamil (தமிழ்)</SelectItem>
                <SelectItem value="te">Telugu (తెలుగు)</SelectItem>
                <SelectItem value="mr">Marathi (मराठी)</SelectItem>
                <SelectItem value="gu">Gujarati (ગુજરાતી)</SelectItem>
                <SelectItem value="kn">Kannada (ಕನ್ನಡ)</SelectItem>
                <SelectItem value="ml">Malayalam (മലയാളം)</SelectItem>
                <SelectItem value="pa">Punjabi (ਪੰਜਾਬੀ)</SelectItem>
                <SelectItem value="or">Odia (ଓଡ଼ିଆ)</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Voice Gender */}
          <div className="grid gap-2">
            <Label htmlFor="voice-gender">Voice Gender</Label>
            <Select value={voiceGender} onValueChange={(v: any) => setVoiceGender(v)}>
              <SelectTrigger id="voice-gender">
                <SelectValue placeholder="Select voice gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="male">Male</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Student Level */}
          <div className="grid gap-2">
            <Label htmlFor="student-level">Student Level</Label>
            <Select value={studentLevel} onValueChange={(v: any) => setStudentLevel(v)}>
              <SelectTrigger id="student-level">
                <SelectValue placeholder="Select student level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Regional References Toggle */}
          <div className="flex items-center justify-between">
            <Label htmlFor="regional-references" className="flex flex-col gap-1">
              <span>Include Regional References</span>
              <span className="text-xs text-muted-foreground font-normal">
                Add region-specific examples and cultural context
              </span>
            </Label>
            <Switch
              id="regional-references"
              checked={includeRegionalReferences}
              onCheckedChange={setIncludeRegionalReferences}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              "Generate Narration"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default GenerateNarrationButton;
