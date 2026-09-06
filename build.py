"""
Regenerates index.html for the Eucalyptus monthly user feedback page.

It reads template.html as the design reference, asks Claude (with web search)
to research the previous full month's public reviews, and writes a fresh
index.html in the same layout. Run by the monthly GitHub Action, and can also
be run by hand.

Needs the ANTHROPIC_API_KEY environment variable.
"""

import datetime
from anthropic import Anthropic

# Confirm the current model ID at https://docs.claude.com/en/docs/about-claude/models
MODEL = "claude-sonnet-4-5"

# Edition 01 was August 2026. Editions count up by one each month from there.
EDITION_ANCHOR_YEAR = 2026
EDITION_ANCHOR_MONTH = 8


def previous_month(today):
    """Return a date that falls inside the month before today's month."""
    first_of_this_month = today.replace(day=1)
    return first_of_this_month - datetime.timedelta(days=1)


def edition_number(d):
    return (d.year - EDITION_ANCHOR_YEAR) * 12 + (d.month - EDITION_ANCHOR_MONTH) + 1


def build_prompt(month_name, year, edition, template):
    header = f"""You are compiling the Eucalyptus monthly user feedback page for {month_name} {year}, Edition {edition:02d}.

Eucalyptus is a digital health company. Its brands are:
- Juniper: weight management. Runs in Australia, the UK, Germany, and Japan.
- Pilot: men's health. Australia only.
- Kin: fertility. Australia only.
- Software: skin. Australia only.
- Compound: newer premium product. Australia only.

Your task: use web search to find public user reviews and discussion published during {month_name} {year} across these sources:
- Trustpilot, including the UK Trustpilot page for Juniper.
- The Apple App Store and Google Play.
- ProductReview.com.au and reviews.io.
- Reddit: search reddit.com for mentions of Juniper, and check any subreddits where people discuss it, including weight-loss and GLP-1 medication communities and any Juniper-specific threads.
Then produce a single self-contained HTML page reporting what you found, in exactly the layout of the template below.

Rules for the content:
- Only include review quotes you can actually find, each with its source and a date (exact or approximate) in {month_name} {year}. Quote them exactly. Never invent reviews, scores, names, or dates.
- For non-English reviews, quote the original and put an English translation underneath, the way the template does.
- Report the current public rating scores where you can read them. If a source or a market is not readable this month, say so plainly in the "How we read this" section instead of guessing a number.
- Write in plain, declarative sentences. No em dashes: use commas, colons, or separate sentences. No marketing language.
- In "One thing to watch", pick the single most notable recurring or cross-market issue if there is one. If nothing stands out, say the month was quiet.
- Keep the clinical-team note only if something with a medical or safety angle actually appears in a review this month.
- Reddit posts and comments are not star-rated. Treat them as qualitative signal. Quote them exactly, include the subreddit name and the date, and only use Reddit content that clearly refers to Juniper.
- Tag every item to the correct market using the data-keys attribute. UK Trustpilot and UK Reddit mentions are Juniper UK (jun-uk). If a Reddit mention does not name a market, give it a data-keys value listing all four Juniper markets so it appears under any Juniper filter.

Rules for the format:
- Match the template exactly: same CSS, same section structure, same class names, same data-keys filtering attributes, same sidebar, same JavaScript. Change only the content.
- Set the masthead period and the sidebar edition to "{month_name} {year}" and "Edition {edition:02d}".
- Keep the data-keys attributes correct so the market and brand filters keep working.
- Output only the complete HTML document, starting with <!DOCTYPE html> and ending with </html>. No commentary before or after, and no markdown code fences.

TEMPLATE:
"""
    return header + template


def main():
    today = datetime.date.today()
    period = previous_month(today)
    month_name = period.strftime("%B")
    year = period.year
    edition = edition_number(period)

    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    response = client.messages.create(
        model=MODEL,
        max_tokens=20000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": build_prompt(month_name, year, edition, template)}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")

    start = text.find("<!DOCTYPE html>")
    end = text.rfind("</html>")
    if start == -1 or end == -1:
        raise SystemExit("The model did not return a complete HTML document. Nothing was written.")
    html = text[start:end + len("</html>")]

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote index.html for {month_name} {year} (Edition {edition:02d}).")


if __name__ == "__main__":
    main()
