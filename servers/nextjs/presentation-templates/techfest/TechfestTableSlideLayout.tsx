import React from 'react'
import * as z from "zod";
import TextWithLaTeX from "@/components/TextWithLaTeX";

export const layoutId = 'techfest-table-slide'
export const layoutName = 'Techfest Table Slide'
export const layoutDescription = 'Data table or comparison grid'

const tableSlideSchema = z.object({
    title: z.string().min(3).max(60).default('Key Metrics').meta({
        description: "Table title",
    }),
    headers: z.array(z.string().min(2).max(30)).min(2).max(4).default(['Feature', 'Basic', 'Pro', 'Enterprise']).meta({
        description: "Column headers",
    }),
    rows: z.array(z.array(z.string().min(1).max(50))).min(3).max(6).default([
        ['Users', '10', '100', 'Unlimited'],
        ['Storage', '5GB', '50GB', '500GB'],
        ['Support', 'Email', '24/7 Chat', 'Dedicated Manager'],
        ['API Access', '❌', '✅', '✅'],
        ['Price', '$0', '$49/mo', '$299/mo']
    ]).meta({
        description: "Table rows data",
    })
})

export const Schema = tableSlideSchema
export type TableSlideData = z.infer<typeof tableSlideSchema>

interface TableSlideLayoutProps {
    data?: Partial<TableSlideData>
}

const TechfestTableSlideLayout: React.FC<TableSlideLayoutProps> = ({ data: slideData }) => {
    const headers = slideData?.headers || ['Feature', 'Basic', 'Pro', 'Enterprise'];
    const rows = slideData?.rows || [
        ['Users', '10', '100', 'Unlimited'],
        ['Storage', '5GB', '50GB', '500GB'],
        ['Support', 'Email', '24/7 Chat', 'Dedicated Manager'],
        ['API Access', '❌', '✅', '✅'],
        ['Price', '$0', '$49/mo', '$299/mo']
    ];

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
                    <div className="mb-8">
                        <TextWithLaTeX 
                            as="h1" 
                            content={slideData?.title || 'Key Metrics'} 
                            className="text-5xl font-bold text-blue-900 mb-3"
                        />
                        <div className="w-24 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full"></div>
                    </div>

                    {/* Table */}
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-gradient-to-r from-blue-600 to-blue-500">
                                    {headers.map((header, index) => (
                                        <th key={index} className="px-6 py-4 text-left">
                                            <TextWithLaTeX 
                                                as="span" 
                                                content={header} 
                                                className="text-lg font-bold text-white"
                                            />
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map((row, rowIndex) => (
                                    <tr 
                                        key={rowIndex} 
                                        className={`${rowIndex % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-cyan-50 transition-colors`}
                                    >
                                        {row.map((cell, cellIndex) => (
                                            <td key={cellIndex} className="px-6 py-4 border-t border-gray-200">
                                                <TextWithLaTeX 
                                                    as="span" 
                                                    content={cell} 
                                                    className={`${cellIndex === 0 ? 'font-semibold text-blue-900' : 'text-gray-700'} text-base`}
                                                />
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Bottom Accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-cyan-400"></div>
            </div>
        </>
    )
}

export default TechfestTableSlideLayout
