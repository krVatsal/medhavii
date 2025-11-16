import type { Metadata } from "next";
import localFont from "next/font/local";
import { Roboto, Instrument_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import MixpanelInitializer from "./MixpanelInitializer";
import { LayoutProvider } from "./(presentation-generator)/context/LayoutContext";
import { Toaster } from "@/components/ui/sonner";
const inter = localFont({
  src: [
    {
      path: "./fonts/Inter.ttf",
      weight: "400",
      style: "normal",
    },
  ],
  variable: "--font-inter",
});

const instrument_sans = Instrument_Sans({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-instrument-sans",
});

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-roboto",
});


export const metadata: Metadata = {
  title: "Medhavi - AI-Powered Intelligent Presentation Generator",
  description:
    "Medhavi (मेधावी) - Indian AI presentation generator with multilingual support, regional context, voice narration in 11+ Indian languages. Open-source alternative to Gamma AI, Beautiful AI.",
  keywords: [
    "AI presentation generator",
    "Indian AI presentation tool",
    "multilingual presentations",
    "Hindi presentation generator",
    "Tamil presentation AI",
    "regional language AI",
    "Bhashini voice narration",
    "educational presentations India",
    "data storytelling India",
    "teaching presentations AI",
    "presentation generator",
    "data to presentation",
    "interactive presentations",
    "professional slides",
  ],
  openGraph: {
    title: "Medhavi - AI-Powered Intelligent Presentation Generator",
    description:
      "Medhavi (मेधावी) - Indian AI presentation generator with multilingual support, regional context, voice narration in 11+ Indian languages. Open-source, privacy-first.",
    siteName: "Medhavi",
    images: [
      {
        url: "https://medhavi.ai/medhavi-feature-graphics.png",
        width: 1200,
        height: 630,
        alt: "Medhavi Logo",
      },
    ],
    type: "website",
    locale: "en_IN",
  },

  twitter: {
    card: "summary_large_image",
    title: "Medhavi - AI-Powered Intelligent Presentation Generator",
    description:
      "Medhavi (मेधावी) - Indian AI presentation generator with multilingual support, regional context, voice narration in 11+ Indian languages.",
    images: ["https://medhavi.ai/medhavi-feature-graphics.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${roboto.variable} ${instrument_sans.variable} antialiased`}
      >
        <Providers>
          <MixpanelInitializer>
            <LayoutProvider>
              {children}
            </LayoutProvider>
          </MixpanelInitializer>
        </Providers>
        <Toaster position="top-center" />
      </body>
    </html>
  );
}
