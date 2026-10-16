import { act, fireEvent, render, screen } from "@testing-library/react";
import { messages } from "../messages.pt";
import { Timeline } from "../Timeline";
import { fixture } from "./fixture";

const q = fixture.questions[0]!;
const rows = fixture.judgments.filter((j) => j.question_id === q.id);

function chart() {
  return render(<Timeline title={q.title} positions={q.positions} judgments={rows} divergences={[]} />);
}

describe("timeline dots", () => {
  it("shows a tooltip with the date, the position and the dgsi.pt link on hover", () => {
    chart();
    fireEvent.pointerEnter(screen.getAllByTestId("dot")[0]!);
    const tip = screen.getByRole("dialog");
    expect(tip).toHaveTextContent("Relativo");
    const link = screen.getByRole("link", { name: messages.timelineTip.open });
    expect(link.getAttribute("href")).toMatch(/^https:\/\/www\.dgsi\.pt\//);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("keeps the tooltip while the pointer moves onto it, so the link can be clicked", () => {
    vi.useFakeTimers();
    chart();
    const dot = screen.getAllByTestId("dot")[0]!;
    fireEvent.pointerEnter(dot);
    fireEvent.pointerLeave(dot);
    fireEvent.pointerEnter(screen.getByRole("dialog"));
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.pointerLeave(screen.getByRole("dialog"));
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.queryByRole("dialog")).toBeNull();
    vi.useRealTimers();
  });

  it("pins on click (touch) and closes with the button or Escape", () => {
    chart();
    const dot = screen.getAllByTestId("dot")[0]!;
    fireEvent.click(dot);
    fireEvent.click(screen.getByRole("button", { name: messages.timelineTip.close }));
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(dot);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("never turns a non-dgsi.pt URL into a link", () => {
    render(
      <Timeline
        title={q.title}
        positions={q.positions}
        judgments={[{ ...rows[0]!, url: "javascript:alert(1)" }]}
        divergences={[]}
      />,
    );
    fireEvent.pointerEnter(screen.getAllByTestId("dot")[0]!);
    expect(screen.queryByRole("link")).toBeNull();
  });
});
