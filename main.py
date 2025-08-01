import sympy as sp
from IPython.display import display, Markdown
import matplotlib.pyplot as plt
import numpy as np

class ANOROCEquationGenerator:
    def __init__(self):
        # Define symbols
        self.G = sp.Function('G')(sp.Symbol('\mu\\nu'))
        self.H = sp.Function('H')(sp.Symbol('\mu\\nu'))
        self.V = sp.Function('V')**(sp.Symbol('(string)'))(sp.Symbol('\mu\\nu'))
        self.phi = sp.Function('\\phi')()
        self.K = sp.Symbol('K')
        self.K_tot = sp.Symbol('K_{tot}')
        self.R = sp.Symbol('R')
        self.g_z = sp.Symbol('g_z')
        self.l_5 = sp.Symbol('l_5')
        self.hbar = sp.Symbol("\\hbar'")
        self.Q = sp.Function('Q')(sp.Symbol('\mu\\nu'))
        
        # Initialize equation parts
        self.equation_parts = []
        self.descriptions = []
        
    def add_term(self, term, description):
        self.equation_parts.append(term)
        self.descriptions.append(description)
        
    def build_equation(self):
        # Construct left-hand side (LHS)
        lhs = sum(self.equation_parts[:5])
        
        # Right-hand side (RHS)
        T_eff = sp.Function('T')**(sp.Symbol('(eff)'))(sp.Symbol('\mu\\nu'))
        V_phi = sp.Function('V')(self.phi)
        rhs_terms = [
            sp.exp(-self.phi) * (T_eff + sp.Derivative(self.phi, sp.Symbol('\mu')) * sp.Derivative(self.phi, sp.Symbol('\nu')) - sp.Rational(1,2)*self.G*V_phi),
            8*sp.pi*sp.Symbol('G_N') * (sp.Function('T')**(sp.Symbol('(matter)'))(sp.Symbol('\mu\\nu')) + sp.Symbol('\chi') * sp.Psi(sp.Symbol('\mu')) * sp.Psi(sp.Symbol('\nu')))),
            sp.Symbol('\kappa_{11}^2') * sp.Function('T')**(sp.Symbol('(brane)'))(sp.Symbol('\mu\\nu')).subs(sp.Symbol('4D'), 'reduction')
        ]
        rhs = sum(rhs_terms)
        
        # Final equation
        equation = sp.Eq(lhs, rhs)
        return equation
    
    def explain_step_by_step(self):
        display(Markdown("## ANOROC-String Equation Generation"))
        
        for i, (term, desc) in enumerate(zip(self.equation_parts, self.descriptions)):
            display(Markdown(f"### Step {i+1}: {desc}"))
            display(Markdown(f"**Term added:**"))
            display(term)
            
            # Visualize term contribution
            if 'K' in str(term):
                self._plot_cutoff_behavior()
                
    def _plot_cutoff_behavior(self):
        """Plot the non-perturbative cutoff function."""
        k_vals = np.linspace(0, 5, 100)
        cutoff = 1 - np.exp(-k_vals)
        
        plt.figure(figsize=(8,4))
        plt.plot(k_vals, cutoff, label=r'$(1 - e^{-K/K_{tot}})$')
        plt.xlabel('K/K_tot', fontsize=12)
        plt.ylabel('Cutoff Factor', fontsize=12)
        plt.title('Non-Perturbative Cutoff Behavior')
        plt.legend()
        plt.grid(True)
        plt.show()

# Initialize and build equation
generator = ANOROCEquationGenerator()

# Add terms with explanations
generator.add_term(
    (1 - sp.exp(-generator.K/generator.K_tot)) * generator.G,
    "Non-perturbative cutoff to regularize gravity at Planck scales"
)

generator.add_term(
    generator.R * generator.H,
    "Curvature coupling term for modified gravity effects"
)

generator.add_term(
    generator.g_z**2 * generator.l_5**2 * generator.V,
    "String theory correction from compactified dimensions"
)

generator.add_term(
    generator.hbar * generator.Q,
    "Quantum corrections from 1-loop effects"
)

generator.add_term(
    sp.Function('G')**(8)(sp.Symbol('AB')) * sp.Function('g')**(sp.Symbol('AB'))(4) + generator.H,
    "Higher-dimensional (8D) gravity terms projected to 4D"
)

# Generate and display
final_eq = generator.build_equation()
display(Markdown("## Final ANOROC-String Equation"))
display(final_eq)

# Explain construction
generator.explain_step_by_step()
