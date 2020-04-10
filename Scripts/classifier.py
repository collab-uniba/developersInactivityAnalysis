'''
Created on Mar 19, 2017

@author: Bogdan Vasilescu
@author: Fisher Yu
'''

import re
import os
import yaml
RE_COMMENT = r'^([ \t]*(#|(\\\*)|(\*\*)|(//)|(/\*))|[ \t]*$)'
regex_comment = re.compile(RE_COMMENT)


class BasicFileTypeClassifier:
    
    def __init__(self):
        # File type
        self.SRC = 0
        self.TEST = 1
        self.DOC = 2
        self.CFG_BUILD_OTHER = 3
    
        self.rules = yaml.load(open(os.path.join(os.path.dirname(__file__),'rules.yml')).read(), Loader=yaml.FullLoader)

        # Code change type in diff
        self.CG_CODE = 0
        self.CG_COMMENT = 1
        
        # List of filename extensions from GitHub Linguist
        # https://github.com/github/linguist
        all_extensions = yaml.load(open(os.path.join(os.path.dirname(__file__),'languages.yml')).read(), Loader=yaml.FullLoader)
        popular = yaml.load(open(os.path.join(os.path.dirname(__file__),'popular.yml')).read(), Loader=yaml.FullLoader)
        self.extensions = {}
        for lang in popular:
            if lang in all_extensions:
                self.extensions[lang] = all_extensions[lang]
        
        self.reverse_extensions = {}
        for lang, d in self.extensions.items():
            for ext in d['extensions']:
                self.reverse_extensions.setdefault(ext, set([]))
                self.reverse_extensions[ext].add(lang)


    def labelDiffLine(self, diff_line):
        #NOTE_PT = r'^([ \t]*(#|(\\\*)|(\*\*)|(//)|(/\*))|[ \t]*$)'
        #pt = re.compile(NOTE_PT)
        match = regex_comment.match(diff_line)
        if match:
            return self.CG_COMMENT
        else:
            return self.CG_CODE
    
    
    def labelFile(self, file_name):
        base_name = os.path.basename(file_name)
        root_name, extension = os.path.splitext(base_name)
        
        # Skip .git folder
        if file_name.find("/.git/") != -1:
            return -1
        
        for signal in self.rules['Media']['path']:
            if file_name.find(signal) != -1:
                return self.DOC

        for signal in self.rules['Doc']['path']:
            if file_name.find(signal) != -1:
                return self.DOC
            
        if extension in self.rules['Doc']['extension']:
            return self.DOC
            
        if root_name in self.rules['Doc']['filename']:
            return self.DOC
          
        for signal in self.rules['Test']['path']:
            if file_name.find(signal) != -1:
                return self.TEST
              
        for signal in self.rules['Source']['path']:
            if file_name.find(signal) != -1:
                return self.SRC

        # SRC extensions          
        if extension in self.reverse_extensions:
            return self.SRC
            
#         for signal in self.rules['Config']['path']:
#             if file_name.find(signal) != -1:
#                 return self.CFG_BUILD_OTHER
# 
#         if root_name in self.rules['Config']['filename']:
#             return self.CFG_BUILD_OTHER

        return self.CFG_BUILD_OTHER
        
 

if __name__ == "__main__":
    bc = BasicFileTypeClassifier()
    
    print ('Popular languages:')
    print (sorted(bc.extensions.keys()))
    
    print ('\nC++ extensions:')
    print (bc.extensions['C++']['extensions'])
    
    print ('\nAmbiguous extensions:')
    for ext, langs in bc.reverse_extensions.iteritems():
        if len(langs) > 1:
            print (ext, langs)
    
#     print ('\nLabels:')
#     from folderManager import Folder
#     for f in Folder('/Users/bogdanv/github_clones/numpy').fullFileNames("*", recursive=True):
#         label = bc.labelFile(f)
#         if label >= 0:
#             print f, label