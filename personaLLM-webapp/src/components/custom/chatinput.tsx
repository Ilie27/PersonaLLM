import { Textarea } from "../ui/textarea";
import { cx } from 'classix';
import { Button } from "../ui/button";
import { ArrowUpIcon } from "./icons"
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { useState, useRef } from 'react';

interface ChatInputProps {
    question: string;
    setQuestion: (question: string) => void;
    onSubmit: (text?: string) => void;
    isLoading: boolean;
}

const suggestedActions = [
    {
        title: 'When is my lunch',
        label: 'with Victoria?',
        action: 'When is my lunch with Victoria?',
    },
    {
        title: 'Who confirmed they',
        label: 'are coming to the meeting?',
        action: 'Who confirmed they are coming to the meeting?',
    },
];

export const ChatInput = ({ question, setQuestion, onSubmit, isLoading }: ChatInputProps) => {
    const [showSuggestions, setShowSuggestions] = useState(true);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://localhost:8000/upload", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) throw new Error("Upload failed");
            const json = await res.json();
            toast.success(`Uploaded: ${json.filename}`);
        } catch (err) {
            console.error("Upload error:", err);
            toast.error("Failed to upload file.");
        } finally {
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    return (
        <div className="relative w-full flex flex-col gap-4">
            {showSuggestions && (
                <div className="hidden md:grid sm:grid-cols-2 gap-2 w-full">
                    {suggestedActions.map((suggestedAction, index) => (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            transition={{ delay: 0.05 * index }}
                            key={index}
                            className={index > 1 ? 'hidden sm:block' : 'block'}
                        >
                            <Button
                                variant="ghost"
                                onClick={() => {
                                    const text = suggestedAction.action;
                                    onSubmit(text);
                                    setShowSuggestions(false);
                                }}
                                className="text-left border rounded-xl px-4 py-3.5 text-sm flex-1 gap-1 sm:flex-col w-full h-auto justify-start items-start"
                            >
                                <span className="font-medium">{suggestedAction.title}</span>
                                <span className="text-muted-foreground">
                                    {suggestedAction.label}
                                </span>
                            </Button>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                accept=".txt,.md"
                className="hidden"
                id="file-upload"
            />

            {/* Upload button */}
            <label htmlFor="file-upload" className="text-sm text-blue-500 cursor-pointer ml-1">
                📎 Upload file
            </label>

            <Textarea
                placeholder="Ask something about your conversations..."
                className={cx(
                    'min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none rounded-xl text-base bg-muted',
                )}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();

                        if (isLoading) {
                            toast.error('Please wait for the model to finish its response!');
                        } else {
                            setShowSuggestions(false);
                            onSubmit();
                        }
                    }
                }}
                rows={3}
                autoFocus
            />

            <Button
                className="rounded-full p-1.5 h-fit absolute bottom-2 right-2 m-0.5 border dark:border-zinc-600"
                onClick={() => onSubmit(question)}
                disabled={question.length === 0}
            >
                <ArrowUpIcon size={14} />
            </Button>
        </div>
    );
};
