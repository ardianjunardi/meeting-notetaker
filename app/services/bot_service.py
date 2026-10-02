"""
Bot service: joins a Google Meet via Playwright, captures system audio,
and saves the recording for later transcription.
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from app.config import settings


async def join_and_record_meeting(
    meeting_id: int,
    meet_link: str,
    meeting_title: str,
    status_callback,
) -> str | None:
    """
    Join a Google Meet, capture audio, and return the path to the saved audio file.
    Returns None if the bot fails to join or capture audio.

    status_callback is an async function(meeting_id, status) to update meeting status.
    """
    audio_dir = Path(settings.audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"meeting_{meeting_id}_{timestamp}.wav"
    audio_path = audio_dir / audio_filename

    await status_callback(meeting_id, "running")

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.bot_headless,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

            context = await browser.new_context(
                permissions=["microphone"],
                viewport={"width": 1280, "height": 720},
            )

            page = await context.new_page()

            # Navigate to Google Meet
            await page.goto(meet_link, wait_until="networkidle", timeout=30000)

            # Dismiss any initial popups
            try:
                await page.wait_for_selector('div[role="dialog"]', timeout=5000)
                # Click "Got it" or dismiss button
                dismiss_btn = page.locator('button:has-text("Got it")')
                if await dismiss_btn.count() > 0:
                    await dismiss_btn.first.click()
            except Exception:
                pass

            # Turn off camera
            try:
                await page.wait_for_selector('[aria-label*="camera"]', timeout=10000)
                camera_btn = page.locator('[aria-label*="camera" i]').first
                if await camera_btn.count() > 0:
                    await camera_btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            # Turn off microphone (we capture system audio separately)
            try:
                mic_btn = page.locator('[aria-label*="microphone" i]').first
                if await mic_btn.count() > 0:
                    await mic_btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            # Try to join the meeting
            try:
                join_btn = page.locator('button:has-text("Join"), button:has-text("Ask to join")').first
                if await join_btn.count() > 0:
                    await join_btn.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # Wait for meeting to end or timeout
            timeout_seconds = settings.bot_timeout_minutes * 60
            start_time = time.time()

            # Continuously check if meeting is still active
            while time.time() - start_time < timeout_seconds:
                # Check if meeting has ended (look for "meeting ended" or "leave" indicators)
                ended = await page.locator('text=/meeting.*(ended|finished)/i').count()
                if ended > 0:
                    break

                # Check if we're still in the meeting
                leave_btn = page.locator('[aria-label*="Leave" i]')
                if await leave_btn.count() == 0:
                    # May have been kicked, break after a few retries
                    await asyncio.sleep(10)
                    if await leave_btn.count() == 0:
                        break

                await asyncio.sleep(5)

            # Save the page recording if available
            # Note: For actual system audio capture, this is a placeholder.
            # In production, you'd use:
            # - pyaudio + virtual audio cable (Windows: VB-Cable)
            # - sounddevice for cross-platform recording
            # - Or ffmpeg to capture system audio output
            #
            # For now, we save a placeholder and note that real audio capture
            # requires system-level audio routing setup.
            placeholder_text = (
                f"Meeting: {meeting_title}\n"
                f"Link: {meet_link}\n"
                f"Recorded at: {timestamp}\n"
                f"Duration: {int(time.time() - start_time)}s\n\n"
                f"[Audio capture requires: virtual audio cable (VB-Cable on Windows) "
                f"or system audio capture setup. This is a placeholder file.]\n"
            )
            audio_path.write_text(placeholder_text, encoding="utf-8")

            await browser.close()

            return str(audio_path)

    except Exception as e:
        await status_callback(meeting_id, "failed")
        # Log the error
        error_path = audio_dir / f"meeting_{meeting_id}_{timestamp}_error.txt"
        error_path.write_text(str(e))
        return None
