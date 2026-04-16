import { useState } from "react";
import { useNavigate } from "react-router";
import { login, verifyOtp } from "../services/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import { Zap, Loader2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [showOtpStep, setShowOtpStep] = useState(false);
  const navigate = useNavigate();

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.mfa_required) {
        setShowOtpStep(true);
        toast.info("Security code sent to your email");
      } else {
        toast.success("Login successful!");
        navigate("/");
      }
    } catch (error: any) {
      toast.error(error.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await verifyOtp(email, otp);
      toast.success("Identity verified!");
      navigate("/");
    } catch (error: any) {
      toast.error(error.message || "Invalid or expired code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f0c29] via-[#1a1145] to-[#0f0c29] p-4">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex items-center gap-3"
          >
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Zap size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-white text-2xl font-bold tracking-tight">ResumeAI</h1>
              <p className="text-violet-300/70 text-sm">Smart Recruitment System</p>
            </div>
          </motion.div>
        </div>

        <Card className="border-white/10 bg-white/5 backdrop-blur-xl text-white">
          <AnimatePresence mode="wait">
            {!showOtpStep ? (
              <motion.div
                key="login"
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 20, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <CardHeader>
                  <CardTitle className="text-xl">Welcome back</CardTitle>
                  <CardDescription className="text-gray-400">
                    Enter your credentials to access the recruiter dashboard
                  </CardDescription>
                </CardHeader>
                <form onSubmit={handleLoginSubmit}>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="admin@talentai.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="bg-white/5 border-white/10 focus:border-violet-500/50 transition-colors"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="password">Password</Label>
                      </div>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="bg-white/5 border-white/10 focus:border-violet-500/50 transition-colors"
                        required
                      />
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button 
                      type="submit" 
                      className="w-full bg-violet-600 hover:bg-violet-500 text-white font-semibold py-6 rounded-xl transition-all shadow-lg shadow-violet-900/20"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Checking...
                        </>
                      ) : (
                        "Sign In"
                      )}
                    </Button>
                  </CardFooter>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="otp"
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -20, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <CardHeader>
                  <div className="flex items-center gap-2 mb-2">
                    <button 
                      onClick={() => setShowOtpStep(false)}
                      className="text-white/60 hover:text-white transition-colors"
                    >
                      <ArrowLeft size={16} />
                    </button>
                    <span className="text-xs text-violet-400 font-medium tracking-wider uppercase">Verification</span>
                  </div>
                  <CardTitle className="text-xl">Enter Security Code</CardTitle>
                  <CardDescription className="text-gray-400">
                    We've sent a 6-digit code to <span className="text-white font-medium">{email}</span>
                  </CardDescription>
                </CardHeader>
                <form onSubmit={handleOtpSubmit}>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="otp">6-Digit Code</Label>
                      <Input
                        id="otp"
                        type="text"
                        placeholder="000000"
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        className="bg-white/5 border-white/10 focus:border-violet-500/50 transition-colors text-center text-2xl tracking-[0.5em] font-mono py-8"
                        required
                      />
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button 
                      type="submit" 
                      className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-6 rounded-xl transition-all shadow-lg shadow-emerald-900/20"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        "Verify & Continue"
                      )}
                    </Button>
                  </CardFooter>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
        
        <p className="mt-8 text-center text-gray-500 text-sm">
          Don't have an account? <span className="text-violet-400 hover:text-violet-300 cursor-pointer font-medium transition-colors">Contact system administrator</span>
        </p>
      </div>
    </div>
  );
}
