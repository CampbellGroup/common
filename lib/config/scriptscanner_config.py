class config(object):

    #list in the format (import_path, class_name)
    #scripts = [('Qsim.scripts.experiments.tickle.tickle_experiment', 'ticklescan')
    scripts = [('common.lib.servers.abstractservers.testexp.testexperiment', 'testexperiment')
               ]

    allowed_concurrent = {
    }
    
    launch_history = 1000   
