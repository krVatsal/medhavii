import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';

export const layoutId = 'techfest-intro-slide'
export const layoutName = 'Techfest Intro Slide'
export const layoutDescription = 'Professional intro slide with Techfest and Cograd logo watermarks'

const introSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Welcome to Techfest 2025').meta({
        description: "Main title of the presentation",
    }),
    subtitle: z.string().min(10).max(150).default('Innovation • Technology • Excellence').meta({
        description: "Subtitle or tagline",
    }),
    presenterName: z.string().min(2).max(50).default('Presented by Team').meta({
        description: "Name of the presenter or team",
    }),
    eventDate: z.string().min(2).max(50).default('December 2025').meta({
        description: "Date of the event",
    }),
})

export const Schema = introSlideSchema

export type IntroSlideData = z.infer<typeof introSlideSchema>

interface IntroSlideLayoutProps {
    data?: Partial<IntroSlideData>
}

const TechfestIntroSlideLayout: React.FC<IntroSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap"
                rel="stylesheet"
            />
            
            <div 
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video relative z-20 mx-auto overflow-hidden"
                style={{
                    background: "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
                    fontFamily: "Poppins, sans-serif"
                }}
            >
                {/* Geometric Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute bottom-0 right-0 w-96 h-96 bg-cyan-400 rounded-full blur-3xl"></div>
                </div>

                {/* Logo Watermarks in Upper Corners */}
                <div className="absolute top-6 left-8 right-8 flex justify-between items-start z-30">
                    {/* Techfest Logo - Top Left */}
                    <div className="w-20 h-20 bg-white/90 backdrop-blur-sm rounded-lg p-2 shadow-xl border border-white/30">
                        <img
                            src="/techfest_logo.png"
                            alt="Techfest Logo"
                            className="w-full h-full object-contain"
                        />
                    </div>

                    {/* Cograd Logo - Top Right */}
                    <div className="w-32 h-20 bg-white rounded-lg p-2 shadow-xl border border-blue-200">
                        <img
                            src="/cograd_logo.png"
                            alt="Cograd Logo"
                            className="w-full h-full object-contain"
                        />
                    </div>
                </div>

                {/* Main Content */}
                <div className="relative z-10 flex flex-col items-center justify-center h-full px-16 text-center">
                    {/* Title */}
                    <TextWithLaTeX 
                        as="h1" 
                        content={slideData?.title || 'Welcome to Techfest 2025'} 
                        className="text-7xl font-extrabold text-white leading-tight mb-6 drop-shadow-2xl"
                    />

                    {/* Accent Line */}
                    <div className="w-40 h-1.5 bg-gradient-to-r from-cyan-400 to-blue-300 rounded-full mb-8 shadow-lg"></div>

                    {/* Subtitle */}
                    <TextWithLaTeX 
                        as="h2" 
                        content={slideData?.subtitle || 'Innovation • Technology • Excellence'} 
                        className="text-3xl font-semibold text-cyan-100 mb-12 tracking-wide"
                    />

                    {/* Presenter Info Card */}
                    <div className="bg-white/15 backdrop-blur-md rounded-2xl px-10 py-6 border-2 border-white/30 shadow-2xl">
                        <div className="flex flex-col items-center gap-3">
                            <TextWithLaTeX 
                                as="div" 
                                content={slideData?.presenterName || 'Presented by Team'} 
                                className="text-2xl font-bold text-white"
                            />
                            <div className="flex items-center gap-3 text-cyan-100">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                <TextWithLaTeX 
                                    as="span" 
                                    content={slideData?.eventDate || 'December 2025'} 
                                    className="text-lg font-medium"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-600 via-cyan-400 to-blue-600"></div>
            </div>
        </>
    )
}

export default TechfestIntroSlideLayout
