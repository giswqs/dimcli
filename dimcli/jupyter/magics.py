"""
Dimcli magic commands used with iPython / Jupyter environments only. See also: https://api-lab.dimensions.ai/cookbooks/1-getting-started/4-Dimcli-magic-commands.html

NOTE All magic commands results get saved automatically to a variable named ``dsl_last_results``.

"""

from IPython.core import magic_arguments
from IPython.core.magic import line_magic, cell_magic, line_cell_magic, Magics, magics_class

from ..VERSION import VERSION

from ..core.api import Dsl
from ..core.functions import *
from ..core.auth import get_global_connection, is_logged_in_globally as is_logged_in
from ..utils.all import *


@magics_class
class DslMagics(Magics):

    results_var = "dsl_last_results" # VAR AUTOMATICALLY SET TO LATEST QUERY RESULTS
    dslobject = None


    def _handle_login(self):
        if is_logged_in():
            self.dslobject = Dsl(show_results=False, verbose=True)
            return True
        else:
            return False


    def _handle_query(self, text, loop=False):
        """main procedure after user input"""
       
        # lazy complete
        text = line_add_lazy_return(text)
        text = line_add_lazy_describe(text)

        # RUN QUERY
        if not loop:
            res = self.dslobject.query(text)
            return res
        else:
            res = self.dslobject.query_iterative(text)
            return res
        

    #
    # MAGIC METHODS
    # 


    @line_cell_magic
    def dsl(self, line, cell=None):
        """Magic command to run a single DSL query. 

        Can be used as a single-line (``%dsl``) or multi-line (``%%dsl``) command. Requires an authenticated API session. Results are saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. 
            
        Returns
        -------
        DslDataset
            A Dimcli wrapper object containing JSON data.     

        Example
        -------
        >>> %dsl search publications for "malaria" return publications limit 500

        """
        if self._handle_login():
            if cell:
                line = cell
            data = self._handle_query(line)
            self.shell.user_ns[self.results_var] = data
            return data


    @line_cell_magic
    def dsldf(self, line, cell=None):
        """Magic command to run a single DSL query, results are transformed to a Pandas DataFrame. 

        Can be used as a single-line (``%dsldf``) or multi-line (``%%dsldf``) command. Requires an authenticated API session. Results are saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. 

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing the query results.      

        Example
        -------
        >>> %dsldf search publications for "malaria" return publications limit 500

        """

        if self._handle_login():
            if cell:
                line = cell
            if not line_is_search_query(line):
                print("Sorry - DSL to dataframe magic methods work only with `search` queries.")
                return None
            data = self._handle_query(line).as_dataframe()
            self.shell.user_ns[self.results_var] = data
            return data

    @line_cell_magic
    def dslgsheets(self, line, cell=None):
        """Magic command to run a single DSL query and to save the results to a google sheet.

        NOTE: this method requires preexisting valid Google authentication credentials. See the description of ``utils.export_as_gsheets`` for more information.

        Can be used as a single-line (``%dslgsheets``) or multi-line (``%%dslgsheets``) command. Requires an authenticated API session. Results are also saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. 

        Returns
        -------
        str
            A string representing the google sheet URL.    

        Example
        -------
        >>> %dslgsheets search publications for "malaria" return publications limit 500

        """
        if self._handle_login():
            if cell:
                line = cell
            if not line_is_search_query(line):
                print("Sorry - DSL to dataframe magic methods work only with `search` queries.")
                return None
            data = self._handle_query(line).as_dataframe()
            self.shell.user_ns[self.results_var] = data
            return export_as_gsheets(data, line)

    @line_cell_magic
    def dslloop(self, line, cell=None):
        """Magic command to run a DSL 'loop' (iterative) query. 

        This command automatically loops over all the pages of a results set, until all possible records have been returned.

        Can be used as a single-line (``%dslloop``) or multi-line (``%%dslloop``) command. Requires an authenticated API session. Results are saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. Should not include limit/skip clauses, as those are added automatically during the iterations.

        Returns
        -------
        DslDataset
            A Dimcli wrapper object containing JSON data.     

        Example
        -------
        >>> %dslloop search publications for "malaria" where times_cited > 200 return publications 

        """
        if self._handle_login():
            if cell:
                line = cell
            data = self._handle_query(line, loop=True)
            self.shell.user_ns[self.results_var] = data
            return data


    @line_cell_magic
    def dslloopdf(self, line, cell=None):
        """Magic command to run a DSL 'loop' (iterative) query. Results are automatically transformed to a pandas dataframe.

        Can be used as a single-line (``%dslloopdf``) or multi-line (``%%dslloopdf``) command. Requires an authenticated API session. Results are saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. Should not include limit/skip clauses, as those are added automatically during the iterations.

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing the query results.      

        Example
        -------
        >>> %dslloopdf search publications for "malaria" where times_cited > 200 return publications 

        """
        if self._handle_login():
            if cell:
                line = cell
            if not line_is_search_query(line):
                print("Sorry - DSL to dataframe magic methods work only with `search` queries.")
                return None
            data = self._handle_query(line, loop=True).as_dataframe()
            self.shell.user_ns[self.results_var] = data
            return data

    @line_cell_magic
    def dslloopgsheets(self, line, cell=None):
        """Magic command to run a DSL 'loop' (iterative) query. Results are automatically uploaded to google sheets. 

        NOTE: this method requires preexisting valid Google authentication credentials. See also https://gspread.readthedocs.io/en/latest/oauth2.html and the description of ``utils.export_as_gsheets`` for more information.

        Can be used as a single-line (``%dslloopgsheets``) or multi-line (``%%dslloopgsheets``) command. Requires an authenticated API session. Results are also saved to a variable called ``dsl_last_results``.

        Parameters
        ----------
        line: str
            A valid DSL search query. Should not include limit/skip clauses, as those are added automatically during the iterations.

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing the query results.      

        Example
        -------
        >>> %dslloopdf search publications for "malaria" where times_cited > 200 return publications 
        """
        if self._handle_login():
            if cell:
                line = cell
            if not line_is_search_query(line):
                print("Sorry - DSL to dataframe magic methods work only with `search` queries.")
                return None
            data = self._handle_query(line, loop=True).as_dataframe()
            self.shell.user_ns[self.results_var] = data
            return export_as_gsheets(data, line)


    @line_cell_magic
    def extract_concepts(self, line, cell=None):
        """Magic command to run the `extract_concepts` function. Results are transformed to a Pandas DataFrame. Score are included by default.
        
        Parameters
        ----------
        cell: str
            Text to extract concepts from. 

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing the concepts and scores.      

        Example
        -------
        >>> %%extract_concepts 
        ... <text>

        """

        if self._handle_login():
            if cell:
                line = cell
            data = line.replace("\n", "")
            data = extract_concepts(data, scores=True, as_df=True)
            self.shell.user_ns[self.results_var] = data
            return data



    @line_cell_magic
    def identify_experts(self, line, cell=None):
        """Magic command to run the `identify_experts` function. Uses all the default options, takes only the `abstract` argument.
        
        Parameters
        ----------
        cell: str
            Text abstract to use to find experts. 

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing experts details.     

        Example
        -------
        >>> %%identify_experts 
        ... <text>

        """

        if self._handle_login():
            if cell:
                line = cell
            data = line.replace("\n", "")
            data = identify_experts(data)
            self.shell.user_ns[self.results_var] = data
            return data



    @line_magic
    def dsldocs(self, line):
        """Magic command to get DSL documentation about sources and fields.
        
        This is a wrapper around the DSL `describe` function.

        Parameters
        ----------
        line: str, optional
            The DSL source or entity name to get documentation for. If omitted, all the documentation is downloaded.

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe containing the query results.      

        Example
        -------
        >>> %dsldocs publications


        """
        if not self._handle_login():
            return

        try:
            import pandas as pd
            df = pd.DataFrame()
        except:
            print("Sorry this functionality requires the Pandas python library. Please install it first")
            return

        obj = line.strip()
        if obj and obj not in G.entities() and obj not in G.sources():
            sou = " - ".join([x for x in G.sources()])
            ent = " - ".join([x for x in G.entities()])
            print(f"Can't recognize this object. Dimcli knows about:\n Sources=[{sou}] Entities=[{ent}] ")
            # continue anyways
        
        res = self._handle_query(f"describe schema") # same query for all requests (filtering done here)

        if not obj:
            # show data for all sources
            docs_for = G.sources()
            header = "sources"
        elif obj in G.entities():
            # match single entity
            docs_for = [obj]
            header = "entities"
        elif obj in G.sources():
            # match single source
            docs_for = [obj]
            header = "sources"
        else:
            # unknown key: try to match a source (eg for newly published sources)
            docs_for = [obj]
            header = "sources"            

        d = {header: [], 'field': [], 'type': [], 'description':[], 'is_filter':[], 'is_entity': [],  'is_facet':[],}
        for S in docs_for:
            for x in sorted(res.json[header][S]['fields']):
                d[header] += [S]
                d['field'] += [x]
                d['type'] += [res.json[header][S]['fields'][x]['type']]
                d['description'] += [res.json[header][S]['fields'][x]['description']]
                d['is_filter'] += [res.json[header][S]['fields'][x]['is_filter']]
                d['is_facet'] += [res.json[header][S]['fields'][x].get('is_facet', False)]
                d['is_entity'] += [res.json[header][S]['fields'][x].get('is_entity', False)]

        data = df.from_dict(d)
        self.shell.user_ns[self.results_var] = data
        return data




from ..repl.autocompletion import CleverCompleter
from prompt_toolkit.document import Document

def _load_ipython_custom_completers(ipython):
    """

    # TODO 
    # check more Completer behaviour in order to remove extra suggestions eg
    # https://www.programcreek.com/python/example/50972/IPython.get_ipython


    """

    def dslq_completers(self, event):
        """ This should return a list of strings with possible completions.

        Note that all the included strings that don't start with event.symbol
        are removed, in order to not confuse readline.

        eg Typing %%apt foo then hitting tab would yield an event like so: namespace(command='%%apt', line='%%apt foo', symbol='foo', text_until_cursor='%%apt foo')

        https://stackoverflow.com/questions/36479197/ipython-custom-tab-completion-for-user-magic-function

        > https://github.com/ipython/ipython/issues/11878
        """
        # print(dir(event), event)

        # FIXME only first line gets the autocomplete!
        if event.line.startswith("%%"):
            event.line = event.line[1:] #  reduce cell symbol (double %) to line symbol
        for command in ["%dslloopdf", "%dsldf", "%dslloop", "%dsl"]:
            if command in event.line: # first match will return results
                doc = Document(event.line.replace(command, ""))
                c = CleverCompleter()
                res = c.get_completions(doc, None)
                # print(res)
                return [x.text for x in res]
            
    def dsldocs_completers(self, event):
        """ 
        Completer for dsldocs command (= describe)
        """
        # print(dir(event), event)
        command = "%dsldocs"
        if event.line.startswith(command):
            doc = Document(event.line.replace(command, ".docs"))
            c = CleverCompleter()
            res = c.get_completions(doc, None)
            # print(res)
            return [x.text for x in res]           

    
    # loader

    for command in ["%dslloop_to_dataframe", "%dsl_to_dataframe", "%dslloop", "%dsl"]:
        ipython.set_hook('complete_command', dslq_completers, re_key = command)
        ipython.set_hook('complete_command', dslq_completers, re_key = "%" + command)

    ipython.set_hook('complete_command', dsldocs_completers, re_key = "%dsldocs")





try:
    ip = get_ipython()
    ip.register_magics(DslMagics)
    # https://github.com/ipython/ipython/issues/11878#issuecomment-554790961
    ip.Completer.use_jedi = False
    _load_ipython_custom_completers(ip)
except:
    print("WARNING: magics.py could load the ipython environment")








# ****************************************************************************

# 
# MEMOS 
# 

# ARGUMENTS AND LINE MAGICS 
# 
# line magics and arguments don't play well together when you need to parse a line content
# in that case the args parsing throws an error
# hence better to have a cell magic, and pass only the args in the line

# @magic_arguments.magic_arguments()
# @magic_arguments.argument('--endpoint',
#     help='The query endpoint: default is https://app.dimensions.ai'
# )
# @magic_arguments.argument('--user',
#     help='The account username'
# )
# @magic_arguments.argument('--password',
#     help='The account password'
# )
# @magic_arguments.argument('--env',
#     help='The instance name as defined in init.py. Default: live.'
# )


# ****************************************************************************