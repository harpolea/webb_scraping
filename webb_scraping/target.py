import requests

from tqdm import tqdm

import numpy as np

from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re

import os
from io import StringIO

import numpy as np

from astroquery.mast import Observations
from astroquery.simbad import Simbad

from . import calculations as c

class Target:
    """
    Performance of web reconnaisanse on an interesting target.
    
    Attributes:
        :aliases: (list of strings) names by which the target is known in other catalogs.
        :input_name: (str) name of target you're interested in.
        :webb_approved: (bool) whether or not the target has been included in approved webb program.
        :hst_approved: (bool) whether or not the target has been included in a public HST program.
        :webb_proposal_link: (list of strings) if there are associated JWST proposals, these
                              are the associated URLs.
        :webb_proposal_names: (list of strings) if there are associated JWST proposals, these
                              are the associated proposal names.
        :hst_data: (dict) keys are HST proposals, vals are links to associated data producs.
        :exoplanet_archive_data: (dict)
        :arxiv_links: (list) list to PDFs of arxiv papers that have self.input_name or self.aliases in 
                      their abstracts
    
    Methods
    --------
        :__init__: initializes.
        :scrape_all: master run method.
        :find_aliases: finds aliases.
        :search_webb_site: manual scraping, not preferred.
        
        
    """
    
    def __init__(self, input_name):
        # instantiates object
        self.input_name = input_name
        self.aliases = []
        self.webb_approved = None
        self.hst_approved = None
        self.webb_proposal_link = []
        self.webb_proposal_names = []
        self.hst_data = {}
        self.exoplanet_archive_data = {}
        self.arxiv_links = []
        self.planet_properties = None
        
    def scrape_all(self):
        """
        The preferred scraping method.
        This calls all other main scraping methods.
        """
        self.find_aliases()
        self.scrape_arxiv()
        self.scrape_webb_MAST()
        self.scrape_HST()
        self.scrape_planet_properties()
       
    def scrape_planet_properties(self):
        """
        Uses exo_MAST to get planet properties for this target.

        """
        # First, we need to find the "canonical name" of the planet — this is how the parameters
        # can be subsequently searched.
        planet_name = self.input_name
        planet_request = requests.get(
            f'https://exo.mast.stsci.edu/api/v0.1/exoplanets/identifiers/?name={planet_name}')
        
        no_nulls = planet_request.text.replace('null', 'np.nan')
        correct_trues = no_nulls.replace('true', 'True')
        correct_bools = correct_trues.replace('false', 'False')
        planet_names = eval(correct_bools)
        canonical_name = planet_names['canonicalName']

        properties_request = requests.get(
            f'https://exo.mast.stsci.edu/api/v0.1/exoplanets/{str.lower(canonical_name)}/properties')
        
        no_nulls = properties_request.text.replace('null', 'np.nan')
        correct_trues = no_nulls.replace('true', 'True')
        correct_bools = correct_trues.replace('false', 'False')
        planet_properties = eval(correct_bools)[0]
        self.planet_properties = planet_properties
        
        
    def run_all_calculations(self, verbose=False):
        """
        Calculates the TSM and ESM (Kempton+ 18) for this target, using known planet
        properties.
        """
        if not self.planet_properties:
            self.scrape_planet_properties()
        TSM = c.TSM(self.planet_properties, verbose=verbose)
        ESM = c.ESM(self.planet_properties, verbose=verbose)
        self.TSM, self.ESM = TSM, ESM
        
        
    def search_webb_site(self, URL):
        """
        Checks whether self has been approved via GTO or ERS. Needs debugging as missing above targets still.
        Adds any links to webb_proposal_links. changed webb_approved. not validated to ERS.
        """
        if not self.aliases:
            print('Not checking aliases.')
        page = requests.get(URL)

        soup = BeautifulSoup(page.content, 'html.parser')

        all_targets = []

        gto_pages = []
        for link in soup.find_all('a'):
            if link.has_attr('href'):
                str_begin = '/jwst/observing-programs/program-information?id='
                if link.attrs['href'][:48] == str_begin:
                    gto_page = 'http://www.stsci.edu/' + link.attrs['href'] # give better name
                    gto_pages.append(gto_page)

        for gto_page in tqdm(gto_pages, position=0, leave=True):
            ID = gto_page[-4:]
            pdf_link = f'http://www.stsci.edu/jwst/phase2-public/{ID}.pdf'
            urlretrieve(pdf_link, "tmp.pdf")
            text = convert_pdf_to_txt("tmp.pdf")
            start = text.find("Science Target") + len("Science Target")
            end = text.find("ABSTRACT")
            target_table = text[start:end]
            targets = list(set(re.findall(r"""\(\d\)\ (\w+)""", target_table)))
        #         targets += list(set(re.findall(r"""\(\d\)(\w+)""", target_table)))
            targets += list(set(re.findall(r"""\(\d\)\ (\w+-\w+)""", target_table)))
            targets += list(set(re.findall(r"""\(\d\)\ (\w+-\w+-\w+)""", target_table))) # for HAT-P-35, for example
            targets += list(set(re.findall(r"""\(\d\)\ (\w+ \w+)""", target_table)))
            in_targets = [a for a in self.aliases if a in targets]
            if len(in_targets) > 0 and self.input_name in _targets:
                self.webb_approved = True
                self.webb_proposal_links.append(pdf_link)
            os.remove('tmp.pdf')
        if self.webb_approved is None: # has not been changed to True
            self.webb_approved = False
        return
    
    def search_GTO(self):
        """
        Manually scrapes the JWST GTO page.
        """
        URL = 'http://www.stsci.edu/jwst/observing-programs/approved-gto-programs'
        self.search_webb_site(URL)
        
    def search_ERS(self):
        """
        Manually scrapes the JWST ERS page.
        """
        URL = 'http://www.stsci.edu/jwst/observing-programs/approved-ers-programs'
        self.search_webb_site(URL)
        
    def search_webb(self):
        """
        Manually scrapes both the JWST ERS and GTO pages.
        """
        self.search_GTO()
        self.search_ERS()
    
    def find_aliases(self):
        """
        Uses astroquery and Simbad to find any aliases of input_name; these are then 
        put into the self.aliases list.
        """
        try:
            self.aliases = list(Simbad.query_objectids(self.input_name)['ID'])
        except TypeError as e:
            if str(e) == """'NoneType' object is not subscriptable""":
                print(f'SIMBAD could not resolve {self.input_name}. Attempting to scrape ExoFOP.')
                if self.input_name[:3] != 'TIC':
                      print(f'Could not scrape {self.input_name}; please try again after changing input_name to a TICID.')
                else:
                      self.scrape_exoFOP_aliases(self.input_name[5:])
            
    
    def scrape_HST(self):
        """
        Checks MAST for the target's relevant HST proposals/data.
        Modifies hst_approved: if there are observations, sets it to True; otherwise False.
        Appends links to relevant HST data to hst_data.
        """
        obs = Observations.query_object(self.input_name, radius=".02 deg") # should work. waliases
        HST_obs = obs[obs['obs_collection']=='HST']
        if len(HST_obs) > 0:
            self.hst_approved = True
            for ob in HST_obs:
                self.hst_data[ob['obs_title']] = ob['dataURL']
        if self.hst_approved is None:
            self.hst_approved = False
        
    def scrape_webb_MAST(self):
        """
        Checks MAST for the target's relevant JWST proposals/data.
        Modifies webb_approved: if there are relevant proposals, sets it to True; otherwise False.
        Appends the names of these proposals to webb_proposal_names.
        """
        obs = Observations.query_object(self.input_name, radius=".02 deg") # should work. waliases
        JWST_obs = obs[obs['obs_collection']=='JWST']
        if len(JWST_obs) > 0:
            self.webb_approved = True
            for ob in JWST_obs:
                self.webb_proposal_names.append(ob['obs_title'])
        if self.webb_approved is None:
            self.webb_approved = False
        return
        
    
    def scrape_arxiv(self, progress=False):
        """
        Searches through arXiv abstracts for the target.
        Appends links of relevant arXiv pdfs to arxiv_links.
        If progress=True, outputs a tqdm progress bar.
        """
        if self.aliases:
            for alias in tqdm(self.aliases, position=0, leave=True, desc='Scraping arXiv'):
                query_URL = f'https://arxiv.org/search/astro-ph?query={alias}&searchtype=abstract&abstracts=show&order=-announced_date_first&size=50'
                page = requests.get(query_URL)
                soup = BeautifulSoup(page.content, 'html.parser')
                for link in soup.find_all('a'):
                    try:
                        paper = link.get('href')
                        if 'pdf'in paper and paper not in self.arxiv_links:
                            self.arxiv_links.append(paper)
                    except TypeError:
                        continue
        else: # I'm sure there's a more elegant way to do this!
            query_URL = f'https://arxiv.org/search/astro-ph?query={self.input_name}&searchtype=abstract&abstracts=show&order=-announced_date_first&size=50'
            page = requests.get(query_URL)
            soup = BeautifulSoup(page.content, 'html.parser')
            for link in soup.find_all('a'):
                try:
                    paper = link.get('href')
                    if 'pdf'in paper and paper not in self.arxiv_links:
                        self.arxiv_links.append(paper)
                except TypeError:
                    continue
            
    
    def scrape_exoplanet_archive(self):
        if not self.aliases:
            print('Not checking aliases.')
        raise NotImplementedError
    
    
    def scrape_exoFOP_aliases(self, ticid):
        """
        This manually scrapes exoFOP for aliases, given a TICID.
        """
        URL = f'https://exofop.ipac.caltech.edu/tess/target.php?id={ticid}'
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        aliases = soup.find_all('table')[7].td.string.split(', ')
        aliases_formatted = [a if a[0] != ' ' else a[1:] for a in aliases]
        aliases_to_add = [a for a in \
                          tqdm(aliases_formatted, leave=True, position=0, desc='Checking aliases to add') \
                          if a not in self.aliases]
        self.aliases += aliases_to_add
           
        
        