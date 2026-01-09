import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-team-slide'
export const layoutName = 'Techfest Team Slide'
export const layoutDescription = 'Team members or about us showcase'

const teamSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Meet Our Team').meta({
        description: "Slide title",
    }),
    members: z.array(z.object({
        name: z.string().min(3).max(50).meta({ description: "Member name" }),
        role: z.string().min(3).max(60).meta({ description: "Member role/title" }),
        description: z.string().min(10).max(150).optional().meta({ description: "Short bio (optional)" })
    })).min(3).max(6).default([
        { name: 'John Smith', role: 'CEO & Founder', description: 'Visionary leader with 15 years of experience' },
        { name: 'Sarah Johnson', role: 'CTO', description: 'Tech innovator and AI specialist' },
        { name: 'Michael Chen', role: 'Head of Design', description: 'Award-winning designer with a passion for UX' },
        { name: 'Emily Davis', role: 'Marketing Director', description: 'Strategic marketer and brand expert' }
    ]).meta({
        description: "Team members to showcase",
    })
})

export const Schema = teamSlideSchema
export type TeamSlideData = z.infer<typeof teamSlideSchema>

interface TeamSlideLayoutProps {
    data?: Partial<TeamSlideData>
}

const TechfestTeamSlideLayout: React.FC<TeamSlideLayoutProps> = ({ data: slideData }) => {
    const members = slideData?.members || [
        { name: 'John Smith', role: 'CEO & Founder', description: 'Visionary leader with 15 years of experience' },
        { name: 'Sarah Johnson', role: 'CTO', description: 'Tech innovator and AI specialist' },
        { name: 'Michael Chen', role: 'Head of Design', description: 'Award-winning designer with a passion for UX' },
        { name: 'Emily Davis', role: 'Marketing Director', description: 'Strategic marketer and brand expert' }
    ];

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
            
            <div className="w-full rounded-sm max-w-[1280px] shadow-lg max-h-[720px] aspect-video bg-white relative z-20 mx-auto overflow-hidden" style={{ fontFamily: "Poppins, sans-serif" }}>
 

                {/* Main Content */}
                <div className="relative z-10 h-full pt-28 pb-12 px-16">
                    {/* Title */}
                    <div className="mb-10">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Meet Our Team'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full"></div>
                    </div>

                    {/* Team Grid */}
                    <div className={`grid gap-6 ${members.length <= 4 ? 'grid-cols-4' : 'grid-cols-3'}`}>
                        {members.map((member, index) => (
                            <div 
                                key={index}
                                className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl p-6 border border-blue-100 hover:border-blue-300 hover:shadow-lg transition-all duration-300 transform hover:scale-105"
                            >
                                {/* Avatar Placeholder */}
                                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-600 to-cyan-400 flex items-center justify-center text-white text-2xl font-bold mb-4 mx-auto shadow-md">
                                    {member.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                                </div>
                                
                                {/* Name */}
                                <div className="text-center mb-2">
                                    <TextWithLaTeX 
                                        as="h3" 
                                        content={member.name} 
                                        className="text-xl font-bold text-blue-900"
                                    />
                                </div>
                                
                                {/* Role */}
                                <div className="text-center mb-3">
                                    <TextWithLaTeX 
                                        as="p" 
                                        content={member.role} 
                                        className="text-sm font-semibold text-cyan-600"
                                    />
                                </div>
                                
                                {/* Description */}
                                {member.description && (
                                    <div className="text-center">
                                        <TextWithLaTeX 
                                            as="p" 
                                            content={member.description} 
                                            className="text-xs text-gray-600"
                                        />
                                    </div>
                                )}
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

export default TechfestTeamSlideLayout
