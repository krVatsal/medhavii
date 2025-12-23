import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";
import { ImageSchema } from '@/presentation-templates/defaultSchemes';

export const layoutId = 'techfest-image-slide'
export const layoutName = 'Techfest Image Slide'
export const layoutDescription = 'Large image with caption overlay'

const imageSlideSchema = z.object({
    title: z.string().min(3).max(80).default('Visual Showcase').meta({
        description: "Image title or caption",
    }),
    description: z.string().min(10).max(200).default('Showcasing innovation through powerful visuals and design excellence').meta({
        description: "Additional description or context",
    }),
    image: ImageSchema.default({
        __image_url__: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
        __image_prompt__: 'Technology visualization with digital networks and data'
    }).meta({
        description: "Main showcase image",
    })
})

export const Schema = imageSlideSchema
export type ImageSlideData = z.infer<typeof imageSlideSchema>

interface ImageSlideLayoutProps {
    data?: Partial<ImageSlideData>
}

const TechfestImageSlideLayout: React.FC<ImageSlideLayoutProps> = ({ data: slideData }) => {
    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-black relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
                {/* Logo Watermarks */}
                <div className="absolute top-4 left-6 right-6 flex justify-between items-start z-40">
                    <div className="w-16 h-16 bg-white shadow-lg rounded-lg p-1.5">
                        <img src="/techfest_logo.png" alt="Techfest" className="w-full h-full object-contain" />
                    </div>
                    <div className="w-24 h-16 bg-white shadow-lg rounded-lg p-1.5">
                        <img src="/cograd_logo.png" alt="Cograd" className="w-full h-full object-contain" />
                    </div>
                </div>

                {/* Main Image */}
                <div className="absolute inset-0">
                    <img
                        src={slideData?.image?.__image_url__ || ''}
                        alt={slideData?.image?.__image_prompt__ || ''}
                        className="w-full h-full object-cover"
                    />
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
                </div>

                {/* Caption Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-12 z-30">
                    <TextWithLaTeX 
                        as="h1" 
                        content={slideData?.title || 'Visual Showcase'} 
                        className="text-6xl font-bold text-white mb-4 drop-shadow-lg"
                    />
                    <div className="w-32 h-1.5 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full mb-4"></div>
                    <TextWithLaTeX 
                        as="p" 
                        content={slideData?.description || 'Showcasing innovation through powerful visuals and design excellence'} 
                        className="text-2xl text-white/90 max-w-3xl"
                    />
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 z-40"></div>
            </div>
        </>
    )
}

export default TechfestImageSlideLayout
