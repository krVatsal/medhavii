export interface ChartAssignmentResponse {
    title_with_charts: {
        title: string;
        graph_id: string | null;
    }[];
    charts: {
        id: string;
        name: string;
        type: string;
        presentation: string;
        postfix: string | null;
        data: {
            categories: string[];
            series: {
                name: string;
                data: number[];
            }[];
        };
    }[];
}

export interface DeplotResponse {
    presentation_id: string;
    charts: ChartAssignmentResponse;
}

export interface ImageAssetResponse {
  message:string;
  path:string;
  id:string;
}

export type PresentationChatRole = "user" | "assistant";

export interface PresentationChatMessage {
    role: PresentationChatRole;
    content: string;
}

export interface PresentationChatResponse {
    reply: string;
}