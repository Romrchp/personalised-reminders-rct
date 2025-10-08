import re

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, 
    Table, TableStyle, Spacer
)
from reportlab.lib.utils import ImageReader
from html import escape

from xml.sax.saxutils import escape

from src.utils.localization_utils import get_localized_summary_element




def clean_text_for_paragraph(text: str) -> str:
    """Enhanced text cleaning with better formatting and proper line break handling"""

    text = escape(text)
    
    # Accounting for line breaks differences in HTML
    text = re.sub(r'<br/></br>', '<br/>', text)
    text = re.sub(r'</br>', '', text) 
    text = re.sub(r'<br\s*/?>', '<br/>', text)
    
    # for bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # for italic text (not used) #TODO : Remove italic.  
    text = re.sub(r'__(.+?)__', r'<i>\1</i>', text)
    # for bullet points
    text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)

    #for line breaks strings --> HTML
    text = re.sub(r'\n\s*\n', '<br/><br/>', text)  
    text = re.sub(r'\n', '<br/>', text) 
    
    return text


def create_hei_footnotes(translations):
    """Create language-flexible footnotes for the HEI table"""
    
    footnotes_style = ParagraphStyle(
        "FootnotesStyle",
        fontSize=8,
        leading=10,
        fontName='Helvetica',
        leftIndent=0,
        rightIndent=0,
        spaceAfter=6
    )
    
    footnotes_text = f"""
        <b>{translations["hei_footnotes"]["notes_title"]}</b><br/>
        <sup>a</sup> {translations["hei_footnotes"]["footnote_a"]}<br/>
        <sup>b</sup> {translations["hei_footnotes"]["footnote_b"]}<br/>
        <sup>c</sup> {translations["hei_footnotes"]["footnote_c"]}<br/>
        <sup>d</sup> {translations["hei_footnotes"]["footnote_d"]}<br/>
        <sup>e</sup> {translations["hei_footnotes"]["footnote_e"]}<br/>
        <sup>f</sup> {translations["hei_footnotes"]["footnote_f"]}<br/>
        {translations["hei_footnotes"]["acronyms_explanation"]}
        """
    
    return Paragraph(footnotes_text, footnotes_style)



def draw_full_page_image(canvas, doc, image_path, user_language):
    """Enhanced image drawing for the user's panels with proper aspect ratio preservation"""
    from PIL import Image as PILImage
    import os
    
    page_width, page_height = A4
    
    # Check if image exists
    if not os.path.exists(image_path):
        canvas.setFont("Helvetica", 16)
        canvas.drawCentredText(page_width/2, page_height/2, "Image not found")
        return
    
    # Draw header
    canvas.setFont("Helvetica-Bold", 18)
    canvas.setFillColor(HexColor("#de7012"))
    header_text = get_localized_summary_element("summary-main-title", user_language)
    text_width = canvas.stringWidth(header_text, "Helvetica-Bold", 18)
    canvas.drawString((page_width - text_width) / 2, page_height - 60, header_text)
    
    # Decorative line under header
    canvas.setStrokeColor(HexColor("#FED7AA"))
    canvas.setLineWidth(2)
    canvas.line(50, page_height - 80, page_width - 50, page_height - 80)
    
    
    try:
        with PILImage.open(image_path) as img:
            img_width, img_height = img.size
    except Exception as e:
        print(f"Error opening image: {e}")
        canvas.setFont("Helvetica", 16)
        canvas.drawCentredText(page_width/2, page_height/2, "Error loading image")
        return
    
    header_space = 100  
    margin = 50  
    available_width = page_width - (2 * margin)
    available_height = page_height - header_space - margin
    
    scale_x = available_width / img_width
    scale_y = available_height / img_height
    
    scale_factor = min(scale_x, scale_y)
    
    final_img_width = img_width * scale_factor
    final_img_height = img_height * scale_factor
    
    # Center the image within available space
    x_offset = (page_width - final_img_width) / 2
    y_offset = (available_height - final_img_height) / 2 + margin
    
    shadow_offset = 3
    canvas.setFillColor(HexColor("#E0E0E0"))
    canvas.rect(x_offset + shadow_offset, y_offset - shadow_offset, 
                final_img_width, final_img_height, fill=1, stroke=0)
    
    canvas.drawImage(ImageReader(image_path), x_offset, y_offset, 
                    width=final_img_width, height=final_img_height)
    
    canvas.setStrokeColor(HexColor("#D0D0D0"))
    canvas.setLineWidth(1)
    canvas.rect(x_offset, y_offset, final_img_width, final_img_height, fill=0, stroke=1)


def create_info_box(content, box_type="info"):
    """Create consistent info boxes with orange theme"""
    return Table([[content]], 
                 colWidths=[6.5 * inch],
                 style=TableStyle([
                     ('BACKGROUND', (0, 0), (-1, -1), HexColor("#FEF7ED")),
                     ('LEFTPADDING', (0, 0), (-1, -1), 15),
                     ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                     ('TOPPADDING', (0, 0), (-1, -1), 12),
                     ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                     ('BOX', (0, 0), (-1, -1), 2, HexColor("#FDBA74")),
                     ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                 ]))


def create_enhanced_disclaimer_box(content, disclaimer_type="default"):
    """Create a disclaimer section with customizable styling based on type"""
    
    if disclaimer_type == "hei-calculation":
        disclaimer_style = ParagraphStyle(
            "HEIDisclaimerStyle",
            fontSize=11,
            leading=13,
            fontName='Helvetica-Bold',
            textColor=HexColor("#DC2626"),  # Red color
            alignment=TA_CENTER,  
            leftIndent=0,
            rightIndent=0,
            spaceAfter=16
        )
    else:
        # Default styling for other disclaimers
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            fontSize=11,
            leading=13,
            fontName='Helvetica',
            textColor=HexColor("#2D3748"),
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=16
        )
    
    clean_content = clean_text_for_paragraph(content)
    disclaimer_para = Paragraph(clean_content, disclaimer_style)
    
    return disclaimer_para



def create_enhanced_hei_explanation_box(content):
    """Create a plain HEI explanation section with nice typography"""
    hei_style = ParagraphStyle(
        "HEIStyle",
        fontSize=11,
        leading=14,
        fontName='Helvetica',
        textColor=HexColor("#1F2937"),
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=16
    )
    
    clean_content = clean_text_for_paragraph(content)
    
    hei_content = f"""{clean_content}"""
    
    hei_para = Paragraph(hei_content, hei_style)
    
    return hei_para



def create_hei_table(translations):
    """Create a language-flexible HEI-2020 components table with translations
    
    Args:
        translations (dict): Dictionary containing translated strings for HEI components
    """

    cell_style = ParagraphStyle(
        "CellStyle",
        fontSize=9,
        leading=11,
        fontName='Helvetica',
    )

    #Creating the table itself
    data = [
        [translations["hei_table"]["component"], translations["hei_table"]["maximum_points"]],
        ["", ""],
        [translations["hei_table"]["adequacy_components"], ""],
        [Paragraph(f"{translations['hei_table']['total_fruits']}<sup>a</sup>", cell_style), "5"],
        [Paragraph(f"{translations['hei_table']['whole_fruits']}<sup>b</sup>", cell_style), "5"],
        [translations["hei_table"]["total_vegetables"], "5"],
        [Paragraph(f"{translations['hei_table']['greens_and_beans']}<sup>c</sup>", cell_style), "5"],
        [Paragraph(translations["hei_table"]["whole_grains"], cell_style), "10"],
        [Paragraph(f"{translations['hei_table']['dairy']}<sup>d</sup>", cell_style), "10"],
        [translations["hei_table"]["total_protein_foods"], "5"],
        [Paragraph(f"{translations['hei_table']['seafood_plant_proteins']}<sup>e</sup>", cell_style), "5"],
        [Paragraph(f"{translations['hei_table']['fatty_acids']}<sup>f</sup>", cell_style), "10"],
        [translations["hei_table"]["moderation_components"], ""],
        [translations["hei_table"]["refined_grains"], "10"],
        [translations["hei_table"]["sodium"], "10"],
        [translations["hei_table"]["added_sugars"], "10"],
        [translations["hei_table"]["saturated_fat"], "10"],
    ]
    
    table = Table(data, colWidths=[4*inch, 1.5*inch])
    
    # Table styleeeeeeeeeeeee
    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#de7012")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        

        ('BACKGROUND', (0, 2), (-1, 2), HexColor("#FED7AA")),
        ('BACKGROUND', (0, 12), (-1, 12), HexColor("#FED7AA")),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (-1, 12), 'Helvetica-Bold'),
        ('SPAN', (0, 2), (-1, 2)),
        ('SPAN', (0, 12), (-1, 12)),
        ('ALIGN', (0, 2), (-1, 2), 'LEFT'),
        ('ALIGN', (0, 12), (-1, 12), 'LEFT'),
        ('FONTSIZE', (0, 2), (-1, 2), 9),
        ('FONTSIZE', (0, 12), (-1, 12), 9),
        
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'), 
        
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#D0D0D0")),
        
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # hide separator rows, looks better
        ('LINEBELOW', (0, 1), (-1, 1), 0, colors.white),
        ('LINEABOVE', (0, 1), (-1, 1), 0, colors.white),
        ('LINEBELOW', (0, 11), (-1, 11), 0, colors.white),
        ('LINEABOVE', (0, 11), (-1, 11), 0, colors.white),
    ]))
    
    return table

def create_section_header(title, is_main=False, is_subsection=False):
    """Create beautiful section headers with decorative elements"""
    if is_main:
        # Main title with orange theme
        return [
            Spacer(1, 0.3 * inch),
            Table([[title]], 
                  colWidths=[7 * inch],
                  style=TableStyle([
                      ('BACKGROUND', (0, 0), (-1, -1), HexColor("#de7012")),
                      ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                      ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                      ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                      ('FONTSIZE', (0, 0), (-1, -1), 16),
                      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                      ('TOPPADDING', (0, 0), (-1, -1), 15),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                      ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                  ])),
            Spacer(1, 0.4 * inch)
        ]
    elif is_subsection:
        # Subsection headers with lighter orange accent
        return [
            Spacer(1, 0.15 * inch),
            Table([["", title]], 
                  colWidths=[0.15 * inch, 6.85 * inch],
                  style=TableStyle([
                      ('BACKGROUND', (0, 0), (0, 0), HexColor("#FDBA74")),
                      ('BACKGROUND', (1, 0), (1, 0), HexColor("#FFFBF5")),
                      ('TEXTCOLOR', (1, 0), (1, 0), HexColor("#4A5568")),
                      ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                      ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                      ('FONTSIZE', (1, 0), (1, 0), 10),
                      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                      ('TOPPADDING', (0, 0), (-1, -1), 6),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                      ('LEFTPADDING', (1, 0), (1, 0), 12),
                  ])),
            Spacer(1, 0.1 * inch)
        ]
    else:
        # Main section headers with orange accent
        return [
            Spacer(1, 0.25 * inch),
            Table([["", title]], 
                  colWidths=[0.2 * inch, 6.8 * inch],
                  style=TableStyle([
                      ('BACKGROUND', (0, 0), (0, 0), HexColor("#de7012")),
                      ('BACKGROUND', (1, 0), (1, 0), HexColor("#FEF7ED")),
                      ('TEXTCOLOR', (1, 0), (1, 0), HexColor("#2D3748")),
                      ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                      ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                      ('FONTSIZE', (1, 0), (1, 0), 12),
                      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                      ('TOPPADDING', (0, 0), (-1, -1), 8),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                      ('LEFTPADDING', (1, 0), (1, 0), 15),
                  ])),
            Spacer(1, 0.15 * inch)
        ]
    
def draw_header_footer(canvas, doc):
    """Draw elegant header and footer"""
    page_width, page_height = A4
    
    # Header - subtle line with orange theme
    canvas.setStrokeColor(HexColor("#FED7AA"))
    canvas.setLineWidth(2)
    canvas.line(50, page_height - 50, page_width - 50, page_height - 50)
    
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#8B8B8B"))
    
    
    # Page number on right
    page_num = canvas._pageNumber
    if page_num > 1:  # Don't show page number on image page
        canvas.drawRightString(page_width - 50, 30, f"Page {page_num - 1}")