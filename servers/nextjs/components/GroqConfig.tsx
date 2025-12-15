"use client";
import { useEffect, useState } from "react";
import { Check, ChevronsUpDown, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "./ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface GroqConfigProps {
  groqApiKey: string;
  groqModel: string;
  onInputChange: (value: string | boolean, field: string) => void;
}

export default function GroqConfig({
  groqApiKey,
  groqModel,
  onInputChange
}: GroqConfigProps) {
  const [openModelSelect, setOpenModelSelect] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsChecked, setModelsChecked] = useState(false);
  const [apiKey, setApiKey] = useState(groqApiKey);

  const groqUrl = "https://api.groq.com/openai/v1";

  useEffect(() => {
    setAvailableModels([]);
    setModelsChecked(false);
    onInputChange("", "groq_model");
  }, [apiKey]);

  const onApiKeyChange = (value: string) => {
    setApiKey(value);
    onInputChange(value, "groq_api_key");
  };

  const fetchAvailableModels = async () => {
    if (!groqApiKey) return;

    setModelsLoading(true);
    try {
      const response = await fetch('/api/v1/ppt/groq/models/available', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: groqUrl,
          api_key: groqApiKey
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data);
        setModelsChecked(true);
        // Default to a common model if available, or the first one
        if (data.length > 0) {
            const defaultModel = data.find((m: string) => m.includes("llama-3.1-70b")) || data[0];
            onInputChange(defaultModel, "groq_model");
        }
      } else {
        console.error('Failed to fetch models');
        setAvailableModels([]);
        setModelsChecked(true);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      toast.error('Error fetching models');
      setAvailableModels([]);
      setModelsChecked(true);
    } finally {
      setModelsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* API Key Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Groq API Key
        </label>
        <div className="relative">
          <input
            type="text"
            value={groqApiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            className="w-full px-4 py-2.5 outline-none border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-colors"
            placeholder="Enter your API key"
          />
        </div>
        <p className="mt-2 text-xs text-gray-500">
          Your API key is stored locally in your browser.
        </p>
      </div>

      {/* Model Selection */}
      {groqApiKey && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model
          </label>
          
          {!modelsChecked ? (
            <Button
              onClick={fetchAvailableModels}
              disabled={modelsLoading}
              className="w-full bg-red-500 hover:bg-red-600 text-white"
            >
              {modelsLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Fetching Models...
                </>
              ) : (
                "Fetch Available Models"
              )}
            </Button>
          ) : (
            <Popover open={openModelSelect} onOpenChange={setOpenModelSelect}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={openModelSelect}
                  className="w-full justify-between"
                >
                  {groqModel
                    ? availableModels.find((model) => model === groqModel)
                    : "Select model..."}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[400px] p-0">
                <Command>
                  <CommandInput placeholder="Search model..." />
                  <CommandList>
                    <CommandEmpty>No model found.</CommandEmpty>
                    <CommandGroup>
                      {availableModels.map((model) => (
                        <CommandItem
                          key={model}
                          value={model}
                          onSelect={(currentValue) => {
                            onInputChange(currentValue === groqModel ? "" : currentValue, "groq_model");
                            setOpenModelSelect(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              groqModel === model ? "opacity-100" : "opacity-0"
                            )}
                          />
                          {model}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          )}
        </div>
      )}
    </div>
  );
}
