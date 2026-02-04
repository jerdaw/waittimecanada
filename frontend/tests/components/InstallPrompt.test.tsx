import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { InstallPrompt } from "../../components/InstallPrompt";

describe("InstallPrompt Component", () => {
  it("does not render initially", () => {
    render(<InstallPrompt />);
    expect(screen.queryByText("Install App")).not.toBeInTheDocument();
  });

  it("renders when beforeinstallprompt event fires", () => {
    render(<InstallPrompt />);
    
    // Simulate event
    const event = new Event("beforeinstallprompt");
    // @ts-ignore
    event.prompt = vi.fn();
    // @ts-ignore
    event.userChoice = Promise.resolve({ outcome: "accepted" });
    
    fireEvent(window, event);
    
    expect(screen.getByText("Install App")).toBeInTheDocument();
  });

  it("calls prompt() when install button clicked", async () => {
    render(<InstallPrompt />);
    
    const event = new Event("beforeinstallprompt");
    const promptSpy = vi.fn();
    // @ts-ignore
    event.prompt = promptSpy;
    // @ts-ignore
    event.userChoice = Promise.resolve({ outcome: "accepted" });
    
    fireEvent(window, event);
    
    fireEvent.click(screen.getByText("Install"));
    
    expect(promptSpy).toHaveBeenCalled();
  });
});
