
def init():
    global na_values
    global algo_list
    na_values = ['Connection to the server lost.  [-10723] PINET: No Connection.',
                 '[-11059] No Good Data For Calculation',
                 '[-11057] Not Enough Values For Calculation',
                 '#DIV/0!', '#VALUE!', '', 'Arc Off-line', '#NUM!',
                 '[-11101] All data events are filtered in summary calculation']
    algo_list = ['lr','plsr','enr','knr','dtr','abr','br','etr']


