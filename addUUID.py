__author__ = 'mart3565'

import os
import uuid
import xml.etree.ElementTree as ET

inputDir = r'C:\Users\mart3565\Desktop\mgs-for-testing'

#count the slashes to get starting depth
startDepth = inputDir.count(os.sep)

for root, dirs ,files in os.walk(inputDir):
    #if beyond one level, don't do anything with files, and delete dir references
    #to avoid recursing further
    if root.count(os.sep) - startDepth > 0:
        del dirs[:]
    else:
        for f in files:
            if f.endswith('.xml'):
                filePath = os.path.join(root,f)
                outPath = os.path.join(root, 'updated', f)
                uniqueID = str(uuid.uuid4())
                tree = ET.parse(filePath)
                content = tree.getroot()
                titleTag = tree.find('.//title')
                titleTag.set('catid', uniqueID)

                ''' Write tree '''
                tree = ET.ElementTree(content)
                tree.write(outPath)

