#!/bin/env python
from pMyMarsUtil import *
import click
import code
"""For starting QuickMARS or SlowMARS
== QuickMARS ==
python StartMarsUtil.py start_quick_mars "Name of source" "Which night in ISO format" "Cut on zenith angle" "Cut on transparency at 9km" "Cut on cloudiness" <Cut on DC in nA> --boolReducedHV
== SlowMARS ==
python StartMarsUtil.py start_slow_mars "Name of source" "Title for this analysis" "Cut on zenith angle" "Cut on transparency at 9km" "Cut on cloudiness" <Cut on DC in nA> --boolReducedHV
"""

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        print ctx.get_help()
    else:
        print('gonna invoke %s' % ctx.invoked_subcommand)


@cli.command(help='start_quick_mars')
@click.argument('strNameSrc')
@click.argument('strTitle')
@click.argument('strZenithCut')
@click.argument('strCutTrans9km')
@click.argument('strCutCloud')
@click.argument('floatCutDCnA')
@click.option('--boolReducedHV', '-rhv', is_flag=True, help='Set True if the data was taken with reduced HV.')
def start_quick_mars(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcnA, boolreducedhv):
    """For night by night quick anlaysis.
start_quick_mars(strNameSrc, strTitle, strCutZenith, strCutTrans9km, strCutCloud, floatCutDCnA, boolReducedHV)
"""
    qma = QuickMARS(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcnA, boolreducedhv)
    print qma


@cli.command(help='start_slow_mars')
@click.argument('strNameSrc')
@click.argument('strTitle')
@click.argument('strZenithCut')
@click.argument('strCutTrans9km')
@click.argument('strCutCloud')
@click.argument('floatcutdcnA')
@click.option('--boolReducedHV', '-rhv', is_flag=True, help='Set True if the data was taken with reduced HV.')
def start_slow_mars(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcnA, boolreducedhv):
    print floatcutdcnA
    sma = SlowMARS(strnamesrc, strtitle, strcutzenith, strcuttrans9km, strcutcloud, floatcutdcnA, boolreducedhv)
    print sma

if __name__ == '__main__': 
    cli()
    code.InteractiveConsole(globals()).interact()
