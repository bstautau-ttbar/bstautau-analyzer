import os, sys

def make_directories_for_plots(basedir, channels, flavor_based=False):
    """Create directories for storing plots in multiple formats and versions."""
    
    print(f"[OUTPUT] Creating directories for plots in {basedir} for channels: {channels}")
    
    signal_scale = ['bstautau_scaled', 'bstautau_not_scaled']
    yscale = ['log', 'lin']
    formats = ['png', 'pdf', 'C', 'root']

    for ch in channels:
        # Sample-based plots
        for s in signal_scale:
            for y in yscale:
                for fmt in formats:
                    os.makedirs(
                        os.path.join(basedir, ch, 'samples_based', s, y, fmt), 
                        exist_ok=True
                    )
        
        if flavor_based:
            # Flavor-based plots
            for s in signal_scale:
                for y in yscale:
                    for fmt in formats:
                        os.makedirs(
                            os.path.join(basedir, ch, 'flavor_based', s, y, fmt), 
                            exist_ok=True
                        )