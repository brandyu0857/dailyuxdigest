def build_email(articles: list[dict], date_str: str) -> str:
    """Build the HTML email from curated articles."""

    # Build article rows
    article_rows = ""
    for i, article in enumerate(articles, 1):
        num = f"{i:02d}"
        title = article.get("title", "Untitled")
        description = article.get("description", "")
        url = article.get("url", "#")
        source = article.get("source", "Read more")
        is_featured = article.get("featured", False) and i == 1

        if is_featured:
            article_rows += f"""
        <tr>
          <td style="padding: 0 40px 12px 40px;">
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 700; color: #ffffff; background-color: #1a1a1a; display: inline-block; padding: 3px 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 1.5px; margin: 0;">Featured</p>
          </td>
        </tr>
        <tr>
          <td style="padding: 0 40px 36px 40px;">
            <h2 style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 22px; font-weight: 700; color: #1a1a1a; margin: 0 0 12px 0; line-height: 1.3;">
              {title}
            </h2>
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; color: #333333; margin: 0 0 14px 0; line-height: 1.6;">
              {description}
            </p>
            <a href="{url}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #0066cc; text-decoration: none; font-weight: 600;">{source} &rarr;</a>
            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 28px 0 0 0;">
          </td>
        </tr>"""
        else:
            article_rows += f"""
        <tr>
          <td style="padding: 0 40px 32px 40px;">
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; color: #999999; margin: 0 0 8px 0; letter-spacing: 0.5px;">{num}</p>
            <h2 style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 0 0 10px 0; line-height: 1.4;">
              {title}
            </h2>
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #444444; margin: 0 0 12px 0; line-height: 1.6;">
              {description}
            </p>
            <a href="{url}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #0066cc; text-decoration: none; font-weight: 500;">{source} &rarr;</a>
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily UX Digest</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; -webkit-font-smoothing: antialiased;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f4;">
    <tr>
      <td align="center" style="padding: 40px 20px;">

        <!-- Main Card -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; max-width: 600px; width: 100%;">

          <!-- Header -->
          <tr>
            <td style="padding: 48px 40px 0 40px;">
              <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; color: #999999; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 12px 0;">Daily Digest</p>
              <h1 style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 28px; font-weight: 700; color: #1a1a1a; margin: 0 0 6px 0;">Design, UX &amp; Product</h1>
              <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #999999; margin: 0 0 24px 0;">{date_str}</p>
              <hr style="border: none; border-top: 1px solid #eeeeee; margin: 0 0 8px 0;">
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td style="padding: 20px 40px 28px 40px;">
              <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #555555; margin: 0; line-height: 1.6;">Here's what's happening in design and product today.</p>
            </td>
          </tr>

          <!-- Articles -->
          {article_rows}

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px 40px 40px; border-top: 1px solid #eeeeee;">
              <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; color: #bbbbbb; margin: 0; text-align: center; line-height: 1.6;">
                Curated daily with AI. You received this because you subscribed to Daily UX Digest.<br>
                <a href="mailto:dailyuxdigest@gmail.com?subject=Unsubscribe&amp;body=Please%20unsubscribe%20me%20from%20Daily%20UX%20Digest." style="color: #bbbbbb; text-decoration: underline;">Unsubscribe</a>
              </p>
            </td>
          </tr>

        </table>
        <!-- End Main Card -->

      </td>
    </tr>
  </table>
</body>
</html>"""

    return html
