import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-closing-slide'
export const layoutName = 'Techfest Closing Slide'
export const layoutDescription = 'Thank you slide with contact information'

const closingSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Thank You!').meta({
        description: "Closing message",
    }),
    subtitle: z.string().min(10).max(150).default("Let's Connect and Innovate Together").meta({
        description: "Subtitle or call to action",
    }),
    contactInfo: z.string().min(10).max(200).default('Contact: info@techfest.org | Visit: www.techfest.org').meta({
        description: "Contact details",
    }),
})

export const Schema = closingSlideSchema

export type ClosingSlideData = z.infer<typeof closingSlideSchema>

interface ClosingSlideLayoutProps {
    data?: Partial<ClosingSlideData>
}

const TechfestClosingSlideLayout: React.FC<ClosingSlideLayoutProps> = ({ data: slideData }) => {
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
                    <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
                    <div className="absolute bottom-0 left-0 w-96 h-96 bg-cyan-400 rounded-full blur-3xl"></div>
                </div>

                {/* Logo Watermarks - Larger on closing slide */}
                <div className="absolute top-8 left-10 right-10 flex justify-between items-start z-30">
                    <div className="w-24 h-24 bg-white/90 backdrop-blur-sm rounded-xl p-3 shadow-xl border border-white/30">
                        <img src="/techfest_logo.png" alt="Techfest" className="w-full h-full object-contain" />
                    </div>
                    <div className="w-36 h-24 bg-white rounded-xl p-3 shadow-xl border border-blue-200">
                        <img src="/cograd_logo.png" alt="Cograd" className="w-full h-full object-contain" />
                    </div>
                </div>

                {/* Main Content */}
                <div className="relative z-10 flex flex-col items-center justify-center h-full px-16 text-center">
                    {/* Thank You Message */}
                    <TextWithLaTeX 
                        as="h1" 
                        content={slideData?.title || 'Thank You!'} 
                        className="text-8xl font-extrabold text-white leading-tight mb-6 drop-shadow-2xl"
                    />

                    {/* Decorative Line */}
                    <div className="w-48 h-1.5 bg-gradient-to-r from-cyan-400 to-blue-300 rounded-full mb-8 shadow-lg"></div>

                    {/* Subtitle */}
                    <TextWithLaTeX 
                        as="h2" 
                        content={slideData?.subtitle || "Let's Connect and Innovate Together"} 
                        className="text-3xl font-semibold text-cyan-100 mb-12 tracking-wide"
                    />

                    {/* Contact Info Card */}
                    <div className="bg-white/15 backdrop-blur-md rounded-2xl px-12 py-8 border-2 border-white/30 shadow-2xl max-w-3xl">
                        <div className="flex flex-col items-center gap-4">
                            {/* Email Icon */}
                            <div className="flex items-center gap-3 text-white">
                                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            
                            <TextWithLaTeX 
                                as="p" 
                                content={slideData?.contactInfo || 'Contact: info@techfest.org | Visit: www.techfest.org'} 
                                className="text-xl text-white font-medium"
                            />
                        </div>
                    </div>

                    {/* Social Media Icons (decorative) */}
                    <div className="flex gap-6 mt-10">
                        {[
                            // Twitter
                            <svg className="w-8 h-8 text-white hover:text-cyan-300 transition-colors cursor-pointer" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z" />
                            </svg>,
                            // LinkedIn
                            <svg className="w-8 h-8 text-white hover:text-cyan-300 transition-colors cursor-pointer" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z" />
                                <circle cx="4" cy="4" r="2" />
                            </svg>,
                            // Instagram
                            <svg className="w-8 h-8 text-white hover:text-cyan-300 transition-colors cursor-pointer" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <rect x="2" y="2" width="20" height="20" rx="5" ry="5" strokeWidth={2} />
                                <path strokeWidth={2} d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37zm1.5-4.87h.01" />
                            </svg>
                        ].map((icon, i) => (
                            <div key={i}>
                                {icon}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-600 via-cyan-400 to-blue-600"></div>
            </div>
        </>
    )
}

export default TechfestClosingSlideLayout
