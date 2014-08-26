class config(object):

    #list in the format (import_path, class_name)
    #scripts = [('Qsim.scripts.experiments.tickle.tickle_experiment', 'ticklescan')
    scripts = [('molecules.lib.exp_control.scripts.scope_periodic', 'ScopeMeasure')
               ]

    allowed_concurrent = {
    }
    
    launch_history = 1000   