import re
import json


def parse_legal_text(file_path):
    """
    Parses a legal text file into a list of dictionaries, where each dictionary
    represents an article with its number, header, and text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    articles = []

    # Regex to find MADDE lines.
    # Group 1: Full "MADDE <number>" (e.g., "MADDE 339")
    # Group 2: Just the number (e.g., "339")
    # Group 3: Text on the MADDE line after "MADDE <number> - " (e.g., "Konut ve...")
    madde_pattern = re.compile(r"^(MADDE\s(\d+))\s*-?\s*(.*)", re.MULTILINE)
    matches = list(madde_pattern.finditer(content))

    # Regex for identifying header lines.
    # Matches lines like:
    # "A. Some Text"
    # "I. Some Roman Numeral Text"
    # "1. Some Numbered Text"
    # "a. Some Lowercase Letter Text"
    # It's designed to pick specific, structured headers.
    header_line_pattern = re.compile(
        r"^\s*(?:[A-ZİÖÜÇŞĞ]\.|[IVXLCDM]+\.|[a-z]\.|\d+\.)\s+[a-zA-Z0-9ğüşıöçĞÜŞİÖÇ\s\(\),'/.:-]+$",
        re.IGNORECASE
    )

    for i, current_match in enumerate(matches):
        article_num_full = current_match.group(1).strip()  # e.g., "MADDE 339"
        text_on_madde_line = current_match.group(3).strip()

        # Determine header for the CURRENT article
        # (Logic for current_article_header remains the same)
        header_search_block_start = 0
        if i > 0:
            header_search_block_start = matches[i-1].end()
        header_search_block_end = current_match.start()
        potential_header_text_block = content[header_search_block_start: header_search_block_end]
        lines_in_header_block = potential_header_text_block.strip().split('\n')
        current_article_header = ""
        for line_idx in range(len(lines_in_header_block) - 1, -1, -1):
            line = lines_in_header_block[line_idx].strip()
            if line:
                if header_line_pattern.match(line) and "MADDE" not in line.upper():
                    current_article_header = line
                    break

        # Determine the actual body text for the CURRENT article
        start_of_body_content = current_match.end()
        end_of_body_content = len(content)  # Default for the last article

        if i + 1 < len(matches):  # If there is a next article
            next_match = matches[i+1]
            next_madde_start_index = next_match.start()

            # Default end for current article's body is the start of the next MADDE line
            end_of_body_content = next_madde_start_index

            # The block of text between the end of the current MADDE line's content
            # and the start of the next MADDE line. This is where the next article's header might be.
            inter_article_text_block = content[start_of_body_content: next_madde_start_index]

            lines_in_inter_block_for_next_header_search = inter_article_text_block.strip().split('\n')
            identified_next_article_header_text = ""

            # Scan backwards from the end of this inter-article block to find the
            # last line that matches the header pattern. This would be the header for the next article.
            for line_idx_next_h in range(len(lines_in_inter_block_for_next_header_search) - 1, -1, -1):
                line_next_h = lines_in_inter_block_for_next_header_search[line_idx_next_h].strip(
                )
                if line_next_h and header_line_pattern.match(line_next_h) and "MADDE" not in line_next_h.upper():
                    identified_next_article_header_text = line_next_h
                    break

            if identified_next_article_header_text:
                # If a header for the next article is found within the inter_article_text_block,
                # the current article's body must end just before this header.
                # We need to find the precise start position of this header text within the original content slice.

                # Iterate through the inter_article_text_block keeping track of char offsets
                # to find the exact start of the identified_next_article_header_text.
                current_offset_in_block = 0
                precise_offset_found = False
                for line_in_block_orig_newlines in inter_article_text_block.splitlines(True):
                    if line_in_block_orig_newlines.strip() == identified_next_article_header_text:
                        # Found the line. The current article's body ends here.
                        end_of_body_content = start_of_body_content + current_offset_in_block
                        precise_offset_found = True
                        break
                    current_offset_in_block += len(line_in_block_orig_newlines)

                # If, for some reason, the precise offset wasn't found (e.g., empty inter_article_text_block after strip for search),
                # the end_of_body_content remains next_madde_start_index, which is a safe fallback.

        actual_article_body_text = content[start_of_body_content:end_of_body_content].strip(
        )

        article_text_parts = []
        if text_on_madde_line:
            article_text_parts.append(text_on_madde_line)
        if actual_article_body_text:  # Add body text only if it's not empty
            article_text_parts.append(actual_article_body_text)

        full_article_text = "\n".join(article_text_parts).strip()

        articles.append({
            'article_number': article_num_full,
            'article_header': current_article_header,
            'text': full_article_text
        })

    return articles


if __name__ == '__main__':
    # Example usage:
    # Make sure the .txt file is in the same directory as the script, or provide the full path.
    file_to_parse = 'TBK_Konut_ve_Catili_Isyeri_Kiralari.txt'
    parsed_articles = parse_legal_text(file_to_parse)

    if parsed_articles:
        print(f"Successfully parsed {len(parsed_articles)} articles.\n")
        # Print details of the first few articles as a sample
        for i, article_data in enumerate(parsed_articles[:3]):
            print(f"--- Article {i+1} ---")
            print(f"  Number: {article_data['article_number']}")
            print(f"  Header: {article_data['article_header']}")
            # Truncate long text for display
            text_preview = (article_data['text'][:150] + '...') if len(
                article_data['text']) > 150 else article_data['text']
            print(f"  Text: {text_preview}")
            print("\n")

        # You can further process or save the 'parsed_articles' list as needed.
        # For example, to save to a JSON file:
        with open('parsed_articles.json', 'w', encoding='utf-8') as outfile:
            json.dump(parsed_articles, outfile, ensure_ascii=False, indent=2)
        print("Parsed articles also saved to parsed_articles.json")

    else:
        print("No articles were parsed.")
