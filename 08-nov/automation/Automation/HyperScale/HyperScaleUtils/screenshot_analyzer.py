# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2021 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""File for converting / matching an image (screenshot) to text

This file consists of a class named: ScreenshotAnalyzer, which can be used for
converting an image to text or matching an image with reference text

All methods are static, so there is no need for instance creation


ScreenshotAnalyzer
=======

    get_text()                      --  Returns the text after analyzing the image
                                        optionally saving .txt file as well

    get_match_score()               --  Returns the percentage match between texts

    match_text()                    --  Returns whether the actual text matches with expected 
                                        list of texts with respect to a threshold

Dependencies:
=======

        tested on pytesseract 0.3.7             (pip)

        tested on rapidfuzz 1.4.1               (pip)

        tested on opencv-4.5.2-vc14_vc15.exe    (external)

        tested on opencv-python 4.5.2.54        (pip)
"""
from rapidfuzz import fuzz
import pytesseract
import cv2
from AutomationUtils import logger
from pathlib import Path

class ScreenshotAnalyzer:
    """
    Given the screenshot path, this class produces text
    and also matches it with reference text
    """
    
    def get_text(image_path, save=True):
        """
        Returns the text after analyzing the image
        optionally saving .txt file as well

        Args:
            image_path  (str)  -- The image file path

            save        (bool) -- Whether to save output text
                                  in a .txt file along with image

        Returns:
            text        (str)  -- The text from the image
        
        Raises Exception:
            If image_path doesn't exist

        """
        path_obj = Path(image_path)
        if not path_obj.exists():
            raise(f"{image_path} doesn't exist. Can't analyze")
        
        txt_path = str(path_obj.with_suffix('.txt'))

        img = cv2.imread(image_path, 0)
        text = pytesseract.image_to_string(img)

        if save:
            with open(txt_path, 'w') as out_file:
                out_file.write(text)
            logger.get_log().info(f"Saved .txt at {txt_path}")

        return text
    
    def get_match_score(actual, expected):
        """
        Returns the percentage match between texts

        Args:
            actual      (str)   -- The actual text present

            expected    (str)   -- The expected or reference text

        Returns:
            percentage  (int)   -- The match percentage (0-100)

        """
        return fuzz.partial_ratio(expected, actual)
    
    def match_text(actual_text, expected_text_list, threshold=90):
        """
        Returns whether the actual text matches with expected 
        list of texts with respect to a threshold

        Args:
            actual_text         (str)   -- The actual text present

            expected_text_list  (list)  -- The list of expected or reference text

        Returns:
            result              (bool)  -- Whether actual text matches with expected list

        """
        for expected in expected_text_list:
            score = ScreenshotAnalyzer.get_match_score(expected, actual_text)
            logger.get_log().info(f'{score}% {expected}')
            if score < threshold:
                return False
        return True

