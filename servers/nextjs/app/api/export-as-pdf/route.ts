import path from "path";
import fs from "fs";
import puppeteer from "puppeteer";

import { sanitizeFilename } from "@/app/(presentation-generator)/utils/others";
import { NextResponse, NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { id, title } = await req.json();
    console.log("[PDF Export] Starting PDF generation for ID:", id, "Title:", title);
    
    if (!id) {
      return NextResponse.json(
        { error: "Missing Presentation ID" },
        { status: 400 }
      );
    }
    
    console.log("[PDF Export] Launching Puppeteer...");
    const browser = await puppeteer.launch({
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--disable-web-security",
      "--disable-background-timer-throttling",
      "--disable-backgrounding-occluded-windows",
      "--disable-renderer-backgrounding",
      "--disable-features=TranslateUI",
      "--disable-ipc-flooding-protection",
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  page.setDefaultNavigationTimeout(300000);
  page.setDefaultTimeout(300000);

  console.log("[PDF Export] Navigating to pdf-maker page...");
  await page.goto(`http://localhost:3000/pdf-maker?id=${id}`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  console.log("[PDF Export] Page loaded. Waiting for document ready...");
  await page.waitForFunction('() => document.readyState === "complete"', { timeout: 10000 });

  console.log("[PDF Export] Checking for slides container...");
  try {
    // Wait for the presentation slides wrapper
    await page.waitForSelector('#presentation-slides-wrapper', { 
      timeout: 30000 
    });
    console.log("[PDF Export] Container found. Waiting for slides to render...");
    
    // Wait for at least one slide with speaker note attribute
    await page.waitForSelector('[data-speaker-note]', { 
      timeout: 30000 
    });
    
    const slideCount = await page.$$eval('[data-speaker-note]', els => els.length);
    console.log(`[PDF Export] Found ${slideCount} slides. Waiting for images...`);
    
    // Wait for all images (including Pexels/Pixabay) to load
    const imageStats = await page.evaluate(() => {
      const images = Array.from(document.images);
      const total = images.length;
      const loaded = images.filter(img => img.complete && img.naturalHeight !== 0).length;
      return { total, loaded };
    });
    console.log(`[PDF Export] Images: ${imageStats.loaded}/${imageStats.total} loaded`);
    
    // Wait for remaining images with generous timeout
    await page.evaluate(() => {
      return Promise.all(
        Array.from(document.images)
          .filter(img => !img.complete || img.naturalHeight === 0)
          .map(img => new Promise(resolve => {
            if (img.complete && img.naturalHeight !== 0) {
              resolve(null);
            } else {
              img.onload = () => resolve(null);
              img.onerror = () => resolve(null);
              // Max 15s per image for external URLs (Pexels/Pixabay)
              setTimeout(() => resolve(null), 15000);
            }
          }))
      );
    });
    
    console.log("[PDF Export] All images processed. Waiting for final render...");
    await new Promise((resolve) => setTimeout(resolve, 3000));
  } catch (error) {
    console.log("[PDF Export] Warning: Timeout waiting for content:", error);
    // Continue anyway
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  console.log("[PDF Export] Generating PDF...");
  const pdfBuffer = await page.pdf({
    width: "1280px",
    height: "720px",
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  });

  await browser.close();
  console.log("[PDF Export] Browser closed. PDF buffer size:", pdfBuffer.length);

  const sanitizedTitle = sanitizeFilename(title ?? "presentation");
  const exportDir = process.env.APP_DATA_DIRECTORY 
    ? path.join(process.env.APP_DATA_DIRECTORY, "exports")
    : path.join(process.cwd(), "..", "fastapi", "app_data", "exports");
  
  const destinationPath = path.join(exportDir, `${sanitizedTitle}.pdf`);
  
  console.log("[PDF Export] Saving to:", destinationPath);
  await fs.promises.mkdir(path.dirname(destinationPath), { recursive: true });
  await fs.promises.writeFile(destinationPath, pdfBuffer);
  console.log("[PDF Export] ✓ PDF saved successfully!");

  return NextResponse.json({
    success: true,
    path: destinationPath,
    url: `/exports/${sanitizedTitle}.pdf`,
  });
  
  } catch (error) {
    console.error("[PDF Export] ✗ Error generating PDF:", error);
    return NextResponse.json(
      { 
        error: "Failed to generate PDF", 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    );
  }
}
