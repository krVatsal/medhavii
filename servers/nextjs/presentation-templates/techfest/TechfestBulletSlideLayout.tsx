import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-bullet-slide'
export const layoutName = 'Techfest Bullet Points'
export const layoutDescription = 'Slide with title and bullet points with icons'

const bulletSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Highlights').meta({
        description: "Slide title",
    }),
    body: z.array(z.object({
        heading: z.string().min(3).max(80).meta({ description: "Bullet point heading" }),
        description: z.string().min(10).max(200).meta({ description: "Bullet point details" })
    })).min(3).max(6).default([
        { heading: "Advanced Technology", description: "Cutting-edge solutions powered by AI and machine learning" },
        { heading: "Seamless Integration", description: "Easy integration with existing tools and workflows" },
        { heading: "24/7 Support", description: "Round-the-clock technical assistance and customer service" },
        { heading: "Scalable Infrastructure", description: "Grows with your business needs effortlessly" }
    ]).meta({
        description: "List of key points with headings and descriptions",
    })
})

export const Schema = bulletSlideSchema

export type BulletSlideData = z.infer<typeof bulletSlideSchema>

interface BulletSlideLayoutProps {
    data?: Partial<BulletSlideData>
}

const TechfestBulletSlideLayout: React.FC<BulletSlideLayoutProps> = ({ data: slideData }) => {
    const bullets = slideData?.body || [
        { heading: "Advanced Technology", description: "Cutting-edge solutions powered by AI and machine learning" },
        { heading: "Seamless Integration", description: "Easy integration with existing tools and workflows" },
        { heading: "24/7 Support", description: "Round-the-clock technical assistance and customer service" },
        { heading: "Scalable Infrastructure", description: "Grows with your business needs effortlessly" }
    ];

    const icons = [
        // Rocket icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>,
        // Puzzle icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
        </svg>,
        // Support icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>,
        // Chart icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>,
        // Star icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>,
        // Shield icon
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
    ];

    return (
        <>
            <link
                href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
                rel="stylesheet"
            />
            
            <div 
                className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-gradient-to-br from-gray-50 to-blue-50 relative z-20 mx-auto overflow-hidden"
                style={{ fontFamily: "Poppins, sans-serif" }}
            >
 

                {/* Main Content */}
                <div className="relative z-10 h-full pt-28 pb-12 px-16">
                    {/* Title */}
                    <div className="mb-10">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Key Highlights'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full"></div>
                    </div>

                    {/* Bullet Points Grid */}
                    <div className="grid grid-cols-2 gap-6">
                        {bullets.map((bullet, index) => (
                            <div 
                                key={index}
                                className="flex gap-4 items-start p-5 bg-white rounded-xl shadow-md border border-blue-100 hover:shadow-lg transition-shadow"
                            >
                                {/* Icon */}
                                <div className="flex-shrink-0 w-14 h-14 bg-gradient-to-br from-blue-600 to-cyan-400 rounded-lg flex items-center justify-center text-white shadow-md">
                                    {icons[index % icons.length]}
                                </div>
                                
                                {/* Content */}
                                <div className="flex-1">
                                    <TextWithLaTeX 
                                        as="h3" 
                                        content={bullet.heading} 
                                        className="text-xl font-bold text-blue-900 mb-2"
                                    />
                                    <TextWithLaTeX 
                                        as="p" 
                                        content={bullet.description} 
                                        className="text-sm text-gray-600 leading-relaxed"
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestBulletSlideLayout
