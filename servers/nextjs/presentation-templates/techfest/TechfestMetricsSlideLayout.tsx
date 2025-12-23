import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-metrics-slide'
export const layoutName = 'Techfest Metrics Slide'
export const layoutDescription = 'Statistics and numbers dashboard'

const metricsSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Our Impact').meta({
        description: "Slide title",
    }),
    metrics: z.array(z.object({
        value: z.string().min(1).max(20).meta({ description: "Metric value (e.g. '500+', '2.5M')" }),
        label: z.string().min(3).max(50).meta({ description: "Metric description" }),
        icon: z.string().optional().meta({ description: "Emoji or icon (optional)" })
    })).min(3).max(6).default([
        { value: '500+', label: 'Active Users', icon: '👥' },
        { value: '98%', label: 'Satisfaction Rate', icon: '⭐' },
        { value: '2.5M', label: 'Downloads', icon: '📱' },
        { value: '150+', label: 'Countries', icon: '🌍' }
    ]).meta({
        description: "Key metrics to display",
    })
})

export const Schema = metricsSlideSchema
export type MetricsSlideData = z.infer<typeof metricsSlideSchema>

interface MetricsSlideLayoutProps {
    data?: Partial<MetricsSlideData>
}

const TechfestMetricsSlideLayout: React.FC<MetricsSlideLayoutProps> = ({ data: slideData }) => {
    const metrics = slideData?.metrics || [
        { value: '500+', label: 'Active Users', icon: '👥' },
        { value: '98%', label: 'Satisfaction Rate', icon: '⭐' },
        { value: '2.5M', label: 'Downloads', icon: '📱' },
        { value: '150+', label: 'Countries', icon: '🌍' }
    ];

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
                {/* Logo Watermarks */}
                <div className="absolute top-4 left-6 right-6 flex justify-between items-start z-30">
                    <div className="w-20 h-20 bg-white shadow-lg rounded-lg p-2 border border-gray-200">
                        <img src="/techfest_logo.png" alt="Techfest" className="w-full h-full object-contain opacity-90" />
                    </div>
                    <div className="w-28 h-20 bg-white shadow-lg rounded-lg p-2 border border-blue-100">
                        <img src="/cograd_logo.png" alt="Cograd" className="w-full h-full object-contain opacity-90" />
                    </div>
                </div>

                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-5">
                    <div className="absolute top-0 left-0 w-full h-full" style={{
                        backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
                        backgroundSize: '40px 40px'
                    }}></div>
                </div>

                {/* Main Content */}
                <div className="relative z-10 h-full pt-28 pb-12 px-16">
                    {/* Title */}
                    <div className="mb-12 text-center">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Our Impact'} 
                            className="text-5xl font-bold text-white mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full mx-auto"></div>
                    </div>

                    {/* Metrics Grid */}
                    <div className={`grid gap-8 ${metrics.length <= 4 ? 'grid-cols-4' : 'grid-cols-3'}`}>
                        {metrics.map((metric, index) => (
                            <div 
                                key={index}
                                className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 hover:bg-white/20 hover:border-cyan-400/50 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl"
                            >
                                {/* Icon */}
                                {metric.icon && (
                                    <div className="text-5xl mb-4 text-center">
                                        {metric.icon}
                                    </div>
                                )}
                                
                                {/* Value */}
                                <div className="text-center mb-3">
                                    <TextWithLaTeX 
                                        as="p" 
                                        content={metric.value} 
                                        className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent"
                                    />
                                </div>
                                
                                {/* Label */}
                                <div className="text-center">
                                    <TextWithLaTeX 
                                        as="p" 
                                        content={metric.label} 
                                        className="text-base font-medium text-gray-200"
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestMetricsSlideLayout
