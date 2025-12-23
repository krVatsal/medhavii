import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-timeline-slide'
export const layoutName = 'Techfest Timeline Slide'
export const layoutDescription = 'Process or timeline visualization'

const timelineSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Our Journey').meta({
        description: "Main title",
    }),
    steps: z.array(z.object({
        heading: z.string().min(3).max(50).meta({ description: "Step title" }),
        description: z.string().min(10).max(150).meta({ description: "Step description" })
    })).min(3).max(5).default([
        { heading: "Phase 1", description: "Research and planning" },
        { heading: "Phase 2", description: "Development and testing" },
        { heading: "Phase 3", description: "Launch and deployment" },
        { heading: "Phase 4", description: "Growth and scaling" }
    ]).meta({
        description: "Timeline steps",
    })
})

export const Schema = timelineSlideSchema
export type TimelineSlideData = z.infer<typeof timelineSlideSchema>

interface TimelineSlideLayoutProps {
    data?: Partial<TimelineSlideData>
}

const TechfestTimelineSlideLayout: React.FC<TimelineSlideLayoutProps> = ({ data: slideData }) => {
    const steps = slideData?.steps || [
        { heading: "Phase 1", description: "Research and planning" },
        { heading: "Phase 2", description: "Development and testing" },
        { heading: "Phase 3", description: "Launch and deployment" },
        { heading: "Phase 4", description: "Growth and scaling" }
    ];

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-white relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
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
                    <div className="mb-12">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Our Journey'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full"></div>
                    </div>

                    {/* Timeline */}
                    <div className="relative">
                        {/* Timeline Line */}
                        <div className="absolute top-8 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 via-cyan-400 to-blue-600"></div>

                        {/* Timeline Steps */}
                        <div className="relative flex justify-between items-start">
                            {steps.map((step, index) => (
                                <div key={index} className="flex flex-col items-center" style={{ width: `${100 / steps.length}%` }}>
                                    {/* Circle */}
                                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-600 to-cyan-400 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10 border-4 border-white">
                                        {index + 1}
                                    </div>
                                    
                                    {/* Content */}
                                    <div className="mt-6 text-center px-2">
                                        <TextWithLaTeX 
                                            as="h3" 
                                            content={step.heading} 
                                            className="text-xl font-bold text-blue-900 mb-2"
                                        />
                                        <TextWithLaTeX 
                                            as="p" 
                                            content={step.description} 
                                            className="text-sm text-gray-600"
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestTimelineSlideLayout
