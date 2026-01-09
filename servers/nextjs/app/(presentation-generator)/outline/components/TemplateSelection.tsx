"use client";
import React, { useEffect } from "react";
import { useLayout } from "../../context/LayoutContext";
import TemplateLayouts from "./TemplateLayouts";

import { Template } from "../types/index";

import { getHeader } from "../../services/api/header";
interface TemplateSelectionProps {
  selectedTemplate: Template | null;
  onSelectTemplate: (template: Template) => void;
}

const TemplateSelection: React.FC<TemplateSelectionProps> = ({
  selectedTemplate,
  onSelectTemplate
}) => {
  const {
    getLayoutsByTemplateID,
    getTemplateSetting,
    getAllTemplateIDs,
    getFullDataByTemplateID,
    loading
  } = useLayout();

  const [summaryMap, setSummaryMap] = React.useState<Record<string, { lastUpdatedAt?: number; name?: string; description?: string }>>({});

  useEffect(() => {
    // Fetch custom templates summary to get last_updated_at and template meta for sorting and display
    fetch(`/api/v1/ppt/template-management/summary`, {
      headers: getHeader(),
    })
      .then(res => res.json())
      .then(data => {
        const map: Record<string, { lastUpdatedAt?: number; name?: string; description?: string }> = {};
        if (data && Array.isArray(data.presentations)) {
          for (const p of data.presentations) {
            const slug = `custom-${p.presentation_id}`;
            map[slug] = {
              lastUpdatedAt: p.last_updated_at ? new Date(p.last_updated_at).getTime() : 0,
              name: p.template?.name,
              description: p.template?.description,
            };
          }
        }
        setSummaryMap(map);
      })
      .catch(() => setSummaryMap({}));
  }, []);

  const templates: Template[] = React.useMemo(() => {
    const templates = getAllTemplateIDs();
    if (templates.length === 0) return [];

    const Templates: Template[] = templates
      .filter((templateID: string) => {
        // Filter out template that contain any errored layouts (from custom templates compile/parse errors)
        const fullData = getFullDataByTemplateID(templateID);
        const hasErroredLayouts = fullData.some((fd: any) => (fd as any)?.component?.displayName === "CustomTemplateErrorSlide");
        return !hasErroredLayouts;
      })
      .map(templateID => {
        const settings = getTemplateSetting(templateID);
        const customMeta = summaryMap[templateID];
        const isCustom = templateID.toLowerCase().startsWith("custom-");
        return {
          id: templateID,
          name: isCustom && customMeta?.name ? customMeta.name : templateID,
          description: (isCustom && customMeta?.description) ? customMeta.description : (settings?.description || `${templateID} presentation templates`),
          ordered: settings?.ordered || false,
          default: settings?.default || false,
        };
      });

    // Sort templates to put default first, then by name
    return Templates.sort((a, b) => {
      if (a.default && !b.default) return -1;
      if (!a.default && b.default) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [getAllTemplateIDs, getLayoutsByTemplateID, getTemplateSetting, getFullDataByTemplateID, summaryMap]);

  const inBuiltTemplates = React.useMemo(
    () => templates.filter(g => !g.id.toLowerCase().startsWith("custom-")),
    [templates]
  );
  const customTemplates = React.useMemo(() => {
    const unsorted = templates.filter(g => g.id.toLowerCase().startsWith("custom-"));
    // Sort by last_updated_at desc using summaryMap keyed by template id
    return unsorted.sort((a, b) => (summaryMap[b.id]?.lastUpdatedAt || 0) - (summaryMap[a.id]?.lastUpdatedAt || 0));
  }, [templates, summaryMap]);

  // Auto-select first template when templates are loaded
  useEffect(() => {
    if (templates.length > 0 && !selectedTemplate) {
      const defaultTemplate = templates.find(g => g.default) || templates[0];
      const slides = getLayoutsByTemplateID(defaultTemplate.id);

      onSelectTemplate({
        ...defaultTemplate,
        slides: slides,
      });
    }
  }, [templates, selectedTemplate, onSelectTemplate]);
  useEffect(() => {
    if (loading) {
      return;
    }
    const existingScript = document.querySelector(
      'script[src*="tailwindcss.com"]'
    );
    if (!existingScript) {
      const script = document.createElement("script");
      script.src = "https://cdn.tailwindcss.com";
      script.async = true;
      document.head.appendChild(script);
    }

  }, []);


  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 rounded-lg border border-gray-200 bg-gray-50 animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded mb-3"></div>
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="aspect-video bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <h5 className="text-lg font-medium mb-2 text-gray-700">
            No Templates Available
          </h5>
          <p className="text-gray-600 text-sm">
            No presentation templates could be loaded. Please try refreshing the page.
          </p>
        </div>
      </div>
    );
  }

  const handleTemplateSelection = (template: Template) => {
    const slides = getLayoutsByTemplateID(template.id);
    onSelectTemplate({
      ...template,
      slides: slides,
    });
  }

  return (
    <div className="space-y-8 mb-4">
      {/* Agentic Mode */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Agentic Mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => handleTemplateSelection({ id: 'agentic-auto', name: 'Auto Select', description: 'Let AI choose the best template', ordered: false, default: false, slides: [] })}
            className={`relative p-4 rounded-lg border cursor-pointer transition-all duration-200 ${
              selectedTemplate?.id === 'agentic-auto'
                ? "border-blue-500 bg-blue-50 shadow-md"
                : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
            }`}
          >
            {selectedTemplate?.id === 'agentic-auto' && (
              <div className="absolute top-3 right-3">
                <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            )}
            <div className="mb-3">
              <h6 className="text-base font-medium text-gray-900 mb-1">🤖 Auto Select Template</h6>
              <p className="text-sm text-gray-600">Let AI automatically choose the best template for your presentation</p>
            </div>
            <div className="flex items-center justify-center min-h-[300px] bg-gradient-to-br from-blue-50 to-purple-50 rounded">
              <div className="text-center">
                <div className="text-4xl mb-2">✨</div>
                <div className="text-sm font-medium text-gray-700">AI-Powered Selection</div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm text-gray-500 mt-3">
              <span>Auto mode</span>
              <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-700">
                Flexible
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* In Built Templates */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">In Built Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {inBuiltTemplates.map((template) => (
            <TemplateLayouts
              key={template.id}
              template={template}
              onSelectTemplate={handleTemplateSelection}
              selectedTemplate={selectedTemplate}
            />
          ))}
        </div>
      </div>

      {/* Custom AI Templates */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">Custom AI Templates</h3>
        </div>
        {customTemplates.length === 0 ? (
          <div className="text-sm text-gray-600 py-2">
            No custom templates. Create one from "All Templates" menu.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customTemplates.map((template) => (
              <TemplateLayouts
                key={template.id}
                template={template}
                onSelectTemplate={handleTemplateSelection}
                selectedTemplate={selectedTemplate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateSelection; 