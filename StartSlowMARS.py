#!/bin/env python
from pMyMarsUtil import *
import click
import code
"""For starting SlowMARS
python StartSlowMARS.py "Name of source" "Title for this analysis" "Cut on zenith angle" "Cut on transparency at 9km" "Cut on cloudiness" <Cut on DC in nA> --boolReducedHV
"""

@click.command()
@click.option('--strnamesrc', default="1ES1959+650")
@click.option('--strTitle', default="MonitoringInCycle11")
@click.option('--strCutZenith', default="35to50")
@click.option('--strCutTrans9km', default="No")
@click.option('--strCutCloud', default="45")
@click.option('--floatcutdcnA', type=float, default=2000.)
# @click.argument('strnamesrc')
# @click.argument('strTitle')
# @click.argument('strZenithCut')
# @click.argument('strCutTrans9km')
# @click.argument('strCutCloud')
# @click.argument('floatcutdcnA', type=float)
@click.option('--boolReducedHV', '-rhv', is_flag=True, help='Set True if the data was taken with reduced HV.')
def start_slow_mars(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcna, boolreducedhv):
    sma = SlowMARS(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcna, boolreducedhv)
    print sma
    code.InteractiveConsole(globals()).interact()
#    code.InteractiveConsole(globals()).interact()
#    return _sma

if __name__ == '__main__':
    print "Main function."
    start_slow_mars()
#    sma = start_slow_mars()
#    print sma
#    code.InteractiveConsole(globals()).interact()
