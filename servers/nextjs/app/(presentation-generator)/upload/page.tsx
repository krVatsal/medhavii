import React from "react";

import UploadPage from "./components/UploadPage";
import Header from "@/app/(presentation-generator)/dashboard/components/Header";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Medhavi | Create AI Presentations in Indian Languages",
  description:
    "Create presentations in Hindi, Tamil, Telugu, Bengali, and 11+ Indian languages with regional context and voice narration. Open-source, privacy-first AI presentation generator.",

  keywords: [
    "AI presentation generator India",
    "Hindi presentation maker",
    "multilingual presentations",
    "regional language presentations",
    "voice narration Indian languages",
    "presentation generator",
    "AI presentations",
    "data visualization India",
    "automatic presentation maker",
    "professional slides",
    "data-driven presentations",
    "document to presentation",
    "presentation automation",
    "smart presentation tool",
    "business presentations India",
  ],
  openGraph: {
    title: "Create Presentations in Indian Languages | Medhavi",
    description:
      "Create presentations in Hindi, Tamil, Telugu, Bengali, and 11+ Indian languages with regional context and voice narration. Open-source, privacy-first.",
    type: "website",
    url: "https://medhavi.ai/create",
    siteName: "Medhavi",
  },
  twitter: {
    card: "summary_large_image",
    title: "Create Presentations in Indian Languages | Medhavi",
    description:
      "Create presentations in Hindi, Tamil, Telugu, Bengali, and 11+ Indian languages with regional context and voice narration.",
    site: "@medhaviai",
    creator: "@medhaviai",
  },
  }

const page = () => {
  return (
    <div className="relative">
      <Header />
      <div className="flex flex-col items-center justify-center  py-8">
        <h1 className="text-3xl font-semibold font-instrument_sans">
          Create Presentation{" "}
        </h1>
        {/* <p className='text-sm text-gray-500'>We will generate a presentation for you</p> */}
      </div>

      <UploadPage />
    </div>
  );
};

export default page;
