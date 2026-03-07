import { CheckCircle2 } from 'lucide-react';

interface StepperProps {
    currentStep: number;
    steps: string[];
}

export function Stepper({ currentStep, steps }: StepperProps) {
    return (
        <div className="w-full max-w-2xl mx-auto mb-12">
            <div className="flex items-center justify-between relative">
                {/* Background Track */}
                <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-white/10 rounded-full z-0"></div>

                {/* Active Track */}
                <div
                    className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-gradient-to-r from-accent-cyan to-accent-purple rounded-full z-0 transition-all duration-500 ease-in-out"
                    style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
                ></div>

                {steps.map((step, index) => {
                    const stepNumber = index + 1;
                    const isActive = stepNumber === currentStep;
                    const isCompleted = stepNumber < currentStep;

                    return (
                        <div key={step} className="relative z-10 flex flex-col items-center group">
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${isActive
                                        ? 'bg-bg-primary border-2 border-accent-cyan text-accent-cyan shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-110'
                                        : isCompleted
                                            ? 'bg-gradient-to-r from-accent-cyan to-accent-purple text-white border-none'
                                            : 'bg-bg-primary border border-white/20 text-text-tertiary'
                                    }`}
                            >
                                {isCompleted ? <CheckCircle2 size={20} /> : stepNumber}
                            </div>
                            <span
                                className={`absolute top-12 text-sm whitespace-nowrap font-medium transition-colors ${isActive ? 'text-white' : isCompleted ? 'text-text-secondary' : 'text-text-tertiary'
                                    }`}
                            >
                                {step}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
