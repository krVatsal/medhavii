import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-quote-slide'
export const layoutName = 'Techfest Quote Slide'
export const layoutDescription = 'Testimonial or inspirational quote'

const quoteSlideSchema = z.object({
    quote: z.string().min(20).max(300).default("Innovation distinguishes between a leader and a follower.").meta({
        description: "The quote text",
    }),
    author: z.string().min(3).max(60).default('Steve Jobs').meta({
        description: "Quote author",
    }),
    designation: z.string().min(3).max(80).optional().default('Co-founder, Apple Inc.').meta({
        description: "Author's title or affiliation",
    })
})

export const Schema = quoteSlideSchema
export type QuoteSlideData = z.infer<typeof quoteSlideSchema>

interface QuoteSlideLayoutProps {
    data?: Partial<QuoteSlideData>
}

const TechfestQuoteSlideLayout: React.FC<QuoteSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-gradient-to-br from-blue-900 via-blue-800 to-cyan-700 relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
                {/* Logo Watermarks */}
                <div className="absolute top-4 left-6 right-6 flex justify-between items-start z-30">
                    <div className="w-20 h-20 bg-white shadow-lg rounded-lg p-2 border border-gray-200">
                        <img src="/techfest_logo.png" alt="Techfest" className="w-full h-full object-contain opacity-90" />
                    </div>
                    <div className="w-28 h-20 bg-white shadow-lg rounded-lg p-2 border border-blue-100">
                        <img src="/cograd_logo.png" alt="Cograd" className="w-full h-full object-contain opacity-90" />
                    </div>
                </div>

                {/* Decorative Quote Icons */}
                <div className="absolute top-32 left-16 text-cyan-400 opacity-20" style={{ fontSize: '120px', lineHeight: '1' }}>
                    "
                </div>
                <div className="absolute bottom-24 right-16 text-cyan-400 opacity-20" style={{ fontSize: '120px', lineHeight: '1', transform: 'rotate(180deg)' }}>
                    "
                </div>

                {/* Main Content */}
                <div className="relative z-10 h-full flex flex-col items-center justify-center px-24 py-20">
                    {/* Quote Text */}
                    <div className="mb-12 text-center">
                        <TextWithLaTeX 
                            as="p" 
                            content={slideData?.quote || "Innovation distinguishes between a leader and a follower."} 
                            className="text-4xl font-semibold text-white leading-relaxed italic"
                        />
                    </div>

                    {/* Author Section */}
                    <div className="flex flex-col items-center">
                        <div className="w-16 h-1 bg-cyan-400 mb-6 rounded-full"></div>
                        <TextWithLaTeX 
                            as="p" 
                            content={slideData?.author || 'Steve Jobs'} 
                            className="text-2xl font-bold text-white mb-2"
                        />
                        {slideData?.designation && (
                            <TextWithLaTeX 
                                as="p" 
                                content={slideData.designation} 
                                className="text-lg text-cyan-200"
                            />
                        )}
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestQuoteSlideLayout
