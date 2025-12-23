import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-comparison-slide'
export const layoutName = 'Techfest Comparison Slide'
export const layoutDescription = 'Two-column comparison layout'

const comparisonSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Feature Comparison').meta({
        description: "Main title",
    }),
    leftTitle: z.string().min(2).max(40).default('Option A').meta({
        description: "Left column title",
    }),
    rightTitle: z.string().min(2).max(40).default('Option B').meta({
        description: "Right column title",
    }),
    leftPoints: z.array(z.string().min(5).max(100)).min(3).max(6).default([
        'Cost-effective solution',
        'Quick implementation',
        'Basic features included',
        'Standard support'
    ]).meta({
        description: "Left column points",
    }),
    rightPoints: z.array(z.string().min(5).max(100)).min(3).max(6).default([
        'Premium capabilities',
        'Advanced features',
        'Priority support 24/7',
        'Scalable architecture'
    ]).meta({
        description: "Right column points",
    })
})

export const Schema = comparisonSlideSchema
export type ComparisonSlideData = z.infer<typeof comparisonSlideSchema>

interface ComparisonSlideLayoutProps {
    data?: Partial<ComparisonSlideData>
}

const TechfestComparisonSlideLayout: React.FC<ComparisonSlideLayoutProps> = ({ data: slideData }) => {
    const leftPoints = slideData?.leftPoints || ['Cost-effective solution', 'Quick implementation', 'Basic features included', 'Standard support'];
    const rightPoints = slideData?.rightPoints || ['Premium capabilities', 'Advanced features', 'Priority support 24/7', 'Scalable architecture'];

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-gray-50 relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
                {/* Logo Watermarks */}
                <div className="absolute top-4 left-6 right-6 flex justify-between items-start z-30">
                    <div className="w-16 h-16 bg-white shadow-md rounded-lg p-1.5 border border-gray-200">
                        <img src="/techfest_logo.png" alt="Techfest" className="w-full h-full object-contain opacity-80" />
                    </div>
                    <div className="w-24 h-16 bg-white shadow-md rounded-lg p-1.5 border border-blue-100">
                        <img src="/cograd_logo.png" alt="Cograd" className="w-full h-full object-contain opacity-80" />
                    </div>
                </div>

                {/* Main Content */}
                <div className="relative z-10 h-full pt-28 pb-12 px-16">
                    {/* Title */}
                    <div className="mb-10 text-center">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Feature Comparison'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full mx-auto"></div>
                    </div>

                    {/* Two Column Comparison */}
                    <div className="grid grid-cols-2 gap-6 h-[calc(100%-120px)]">
                        {/* Left Column */}
                        <div className="bg-white rounded-2xl p-8 shadow-lg border-2 border-blue-200">
                            <div className="mb-6 text-center">
                                <TextWithLaTeX 
                                    as="h2" 
                                    content={slideData?.leftTitle || 'Option A'} 
                                    className="text-3xl font-bold text-blue-900"
                                />
                            </div>
                            <div className="space-y-4">
                                {leftPoints.map((point, index) => (
                                    <div key={index} className="flex items-start gap-3">
                                        <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 mt-1">
                                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <TextWithLaTeX as="p" content={point} className="text-lg text-gray-700" />
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Column */}
                        <div className="bg-gradient-to-br from-blue-600 to-cyan-500 rounded-2xl p-8 shadow-lg border-2 border-cyan-300">
                            <div className="mb-6 text-center">
                                <TextWithLaTeX 
                                    as="h2" 
                                    content={slideData?.rightTitle || 'Option B'} 
                                    className="text-3xl font-bold text-white"
                                />
                            </div>
                            <div className="space-y-4">
                                {rightPoints.map((point, index) => (
                                    <div key={index} className="flex items-start gap-3">
                                        <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center flex-shrink-0 mt-1">
                                            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <TextWithLaTeX as="p" content={point} className="text-lg text-white" />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestComparisonSlideLayout
