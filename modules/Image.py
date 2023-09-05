import logging
import cv2
from PIL import ImageFile

from modules.mmf.Emu import get_emu
from modules.mmf.Screenshot import get_screenshot

log = logging.getLogger(__name__)

ImageFile.LOAD_TRUNCATED_IMAGES = True

def detect_template(file: str):
    """
    Return true if template (image) is found anywhere on-screen
    :param file: File location of image to search
    :return: Boolean value of whether image was found
    """
    try:
        threshold = 0.999
        template = cv2.imread(f"./modules/data/templates/" + file, cv2.IMREAD_UNCHANGED)
        
        screenshot = get_screenshot()
        correlation = cv2.matchTemplate(screenshot, template[:, :, 0:3],
                                        cv2.TM_CCORR_NORMED) # Do masked template matching and save correlation image
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(correlation)
        max_val_corr = float('{:.6f}'.format(max_val))
        if max_val_corr > threshold:
            return True
        else:
            return False
    
    except Exception as e:
        log.debug(str(e))
        return False