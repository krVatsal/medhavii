import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';

export const layoutId = 'techfest-content-slide'
export const layoutName = 'Techfest Content Slide'
export const layoutDescription = 'Main content slide with title, body text, and optional image'

const contentSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Features').meta({
        description: "Slide title",
    }),
    body: z.string().min(20).max(500).default('Our platform provides comprehensive solutions for modern challenges. With advanced technology integration, seamless user experience, and robust security features, we deliver exceptional value to our users.').meta({
        description: "Main content text",
    }),
    image: ImageSchema.optional().meta({
        description: "Optional supporting image",
    })
})

export const Schema = contentSlideSchema

export type ContentSlideData = z.infer<typeof contentSlideSchema>

interface ContentSlideLayoutProps {
    data?: Partial<ContentSlideData>
}

const TechfestContentSlideLayout: React.FC<ContentSlideLayoutProps> = ({ data: slideData }) => {
    const hasImage = slideData?.image?.__image_url__;

    return (
        <>
            <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
                rel="stylesheet"
            />
            
            <div 
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-white relative z-20 mx-auto overflow-hidden"
                style={{ fontFamily: "Poppins, sans-serif" }}
            >
 

                {/* Main Content */}
                <div className="relative z-10 h-full pt-28 pb-12 px-16">
                    {/* Title */}
                    <div className="mb-8">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Key Features'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full"></div>
                    </div>

                    {/* Content Area */}
                    <div className={`flex gap-8 ${hasImage ? '' : 'justify-center'}`}>
                        {/* Text Content */}
                        <div className={`${hasImage ? 'flex-1' : 'max-w-4xl'}`}>
                            <TextWithLaTeX 
                                as="p" 
                                content={slideData?.body || 'Our platform provides comprehensive solutions for modern challenges. With advanced technology integration, seamless user experience, and robust security features, we deliver exceptional value to our users.'} 
                                className="text-xl text-gray-700 leading-relaxed"
                            />
                        </div>

                        {/* Optional Image */}
                        {hasImage && (
                            <div className="w-80 h-64 rounded-xl overflow-hidden shadow-lg border-4 border-blue-100">
                                <img
                                    src={slideData?.image?.__image_url__}
                                    alt={slideData?.image?.__image_prompt__ || ''}
                                    className="w-full h-full object-cover"
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestContentSlideLayout
